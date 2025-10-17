"""Type definitions for Frisbo SDK."""

from typing import Literal

# Order fulfillment statuses
FulfillmentStatus = Literal[
    # Processing
    "Processing", "Split", "Split error", "Wms error", "Fulfill error",
    "Error", "Pending awb", "Pending COD approval", "Pending invoice",
    "Pending stock", "Pending cancel", "Pending checks", "External awb",
    "Preparing documents", "Delaying processing", "Stock error",
    "Out of stock", "AWB error", "Invoice error", "Initializing fulfillment",
    "Awaiting fulfillment order", "Pending payment", "Pending fulfillment",
    "Sending to wms", "Postponed",
    # Picking
    "Ready for picking", "In picking", "Waiting for courier.Invoice error",
    "Waiting for courier.Warranty error", "Waiting for courier",
    # Shipping
    "In transit", "Out for delivery", "Customer pickup", "Personal Pickup",
    "Warehouse pickup", "In parcel locker", "Unsuccessful delivery",
    "Partially Delivered", "Incorrect Address", "Delivered", "Refused",
    "Canceled", "Redirected", "Late canceled",
    # Returning
    "Returning to sender", "Received by sender", "Back to sender",
    "Returned", "Partially returned", "Storno failed", "Return error",
    "Back to sender error",
    # Other
    "Archived"
]

# Inbound statuses
InboundStatus = Literal[
    "New", "Declined", "Pending approval", "Sending to WMS", "WMS error",
    "Ready for counting", "Pending Completion", "In progress", "Completed",
    "Completed with differences", "Confirming", "Confirmed",
    "Confirmed with differences", "Confirming error"
]

# Supported couriers
Courier = Literal[
    "123kurier", "acs_gr", "apc", "auto", "brt_it", "cargus",
    "colissimo_fr", "correos_es", "correos_express", "dhl", "dhl_de",
    "dhl_nl", "dhl_uk", "dpd", "dpd_cz", "dpd_de", "dpd_hr", "dpd_hu",
    "dpd_it", "dpd_pl", "dpd_sk", "dpd_uk", "econt", "ecourier",
    "etrak_uk", "evri_uk", "exelot", "fan", "fan_md", "fedex", "foxpost",
    "furdeco", "geis_cz", "gfs", "gls", "gls_at", "gls_cz", "gls_de",
    "gls_hr", "gls_hu", "gls_pl", "gls_sk", "inpost", "mmp", "mock",
    "mrw_es", "muvi", "nemo", "novaposhta", "paack", "packeta",
    "palletforce", "parcel_force_uk", "personal_pickup", "pgs", "post_at",
    "post_cz", "post_de", "post_dk", "post_ee", "post_fr", "post_hr",
    "post_it", "post_lu", "post_nl", "post_pl", "post_sk", "posta_moldovei",
    "postnord", "ppl_cz", "raben", "royal_mail_uk", "sameday", "sameday_hu",
    "sda_it", "shipvam_gr", "speedy", "spring", "sps_sk", "team_courier_ro",
    "tnt", "toyland", "tuffnells", "unknown", "ups", "xp_courier_gr"
]
