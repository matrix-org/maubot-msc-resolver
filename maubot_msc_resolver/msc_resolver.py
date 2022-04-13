from maubot import Plugin, MessageEvent
from mautrix.types.event import MessageType
from maubot.handlers import command
from mautrix.util import markdown
from typing import Optional, Tuple
from attr import dataclass
from aiohttp import ClientResponseError


# The GitHub repository where MSCs are stored
MSC_REPO = "matrix-org/matrix-spec-proposals"
# The GitHub label that denotes an issue as an MSC
PROPOSAL_LABEL = "proposal"


@dataclass
class MSC:
    id: str
    title: str
    author: str
    url: str


class MSCResolverBot(Plugin):
    # Match any text consisting of "msc" with 1 to 4 digits immediately following.
    # Create a match group surrounding those digits (the MSC's ID).
    @command.passive(r"msc(\d{1,4})", case_insensitive=True, multiple=True)
    async def respond_to_message(self, event: MessageEvent, match: Tuple[str]) -> None:
        """
        When a user posts the name of an MSC in a room message, post a new message
        with a direct link to that MSC.

        Args:
            event: The event containing the message.
            match: The matched text within the body of the message event.
        """
        # Ignore events that we've sent
        if event.sender == self.client.mxid:
            return

        # Ignore message edits
        if event.content.get_edit() is not None:
            return

        # Ignore unless the pattern was contained within a text message or an emote.
        # This explicitly ignores "notice" messages, which may be posted by other bots.
        if event.content.msgtype not in (MessageType.TEXT, MessageType.EMOTE):
            return

        # The message may contain multiple msc identifiers.
        # For each mentioned of an MSC, extract just its ID.
        # Ensure that we remove any duplicates while preserving order.
        msc_ids = []
        for _, msc_id in match:
            if msc_id not in msc_ids:
                msc_ids.append(msc_id)

        # Resolve metadata of each MSC from its ID
        mscs = []
        for msc_id in msc_ids:
            self.log.debug(f"Resolving MSC{msc_id} in room {event.room_id} in response to {event.event_id}")

            try:
                msc = await self._resolve_msc(msc_id)
                if msc is None:
                    # Skip issues that are not marked as an MSC
                    continue
            except ClientResponseError as e:
                self.log.error("Failed to query GitHub's API:", e)
                return

            mscs.append(msc)

        if not mscs:
            # We have no MSCs to resolve.
            self.log.debug("No suitable MSCs found. Not responding")
            return

        if len(mscs) > 1:
            # If there are multiple MSCs in the message, compile them into a list
            message = "\n\n".join(
                [
                    self._format_msc(msc, with_id=True)
                    for msc in mscs
                ]
            )
        else:
            # Otherwise, only list one
            message = self._format_msc(mscs[0])

        # Generate and post the message
        self.log.debug(f"Sending response to event {event.event_id}")
        await self.client.send_notice(event.room_id, message, markdown.render(message))

    async def _resolve_msc(self, msc_id: str) -> Optional[MSC]:
        """Given an MSC's ID, return an MSC object.

        Args:
            msc_id: The ID of the MSC.

        Returns:
            An MSC object with useful metadata, or None if the ID did not
            resolve to an MSC.
        """
        # Request MSC information from GitHub's API
        # TODO: Allow authenticated requests
        response = await self.http.get(f"https://api.github.com/repos/{MSC_REPO}/issues/{msc_id}")
        if response.status != 200:
            response.raise_for_status()
        response_body = await response.json()

        # Check if this is a proposal
        is_msc = False
        for label in response_body.get("labels", []):
            if label.get("name") == PROPOSAL_LABEL:
                is_msc = True
                break

        if not is_msc:
            return None

        # Extract MSC information from the API response
        msc_title = response_body.get("title", "Unknown title")
        msc_author = "@" + response_body.get("user", {}).get("login", "Unknown author")
        msc_url = f"https://github.com/{MSC_REPO}/issues/{msc_id}"

        # Build and return an MSC object
        return MSC(
            id=msc_id,
            title=msc_title,
            author=msc_author,
            url=msc_url,
        )

    def _format_msc(self, msc: MSC, with_id: bool = False) -> str:
        """Format an MSC into a human-readable string using its metadata.

        Args:
            msc: The MSC to format.

        Returns:
            A formatted string containing information regarding the MSC.
        """
        formatted_str = f"[{msc.title}]({msc.url}) by {msc.author}"
        if with_id:
            formatted_str = f"MSC{msc.id}: {formatted_str}"

        return formatted_str