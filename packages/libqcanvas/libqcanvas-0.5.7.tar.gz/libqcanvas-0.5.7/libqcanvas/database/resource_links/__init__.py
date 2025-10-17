from .decorators import with_attachments, with_embedded_resources
from .ornamental_mixins import (
    WithAttachmentsOrnamentalMixin,
    WithResourcesOrnamentalMixin,
)
from .resource_link_manipulators import (
    bulk_change_embedded_link_states,
    change_embedded_link_state,
    create_resource_link,
    create_resource_link_a,
    get_associated_resource_ids,
)
