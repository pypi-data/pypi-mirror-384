from .utils.json_map import JsonMap
from .utils.base_model import BaseModel


@JsonMap({"hardware_name": "hardwareName", "hardware_model": "hardwareModel"})
class Device(BaseModel):
    """Device

    :param oem: Name of the OEM
    :type oem: str
    :param hardware_name: Name of the Device
    :type hardware_name: str
    :param hardware_model: Model of the Device
    :type hardware_model: str
    :param eid: Serial Number of the eSIM
    :type eid: str
    """

    def __init__(
        self, oem: str, hardware_name: str, hardware_model: str, eid: str, **kwargs
    ):
        """Device

        :param oem: Name of the OEM
        :type oem: str
        :param hardware_name: Name of the Device
        :type hardware_name: str
        :param hardware_model: Model of the Device
        :type hardware_model: str
        :param eid: Serial Number of the eSIM
        :type eid: str
        """
        self.oem = oem
        self.hardware_name = hardware_name
        self.hardware_model = hardware_model
        self.eid = eid
        self._kwargs = kwargs


@JsonMap({})
class GetEsimDeviceOkResponse(BaseModel):
    """GetEsimDeviceOkResponse

    :param device: device
    :type device: Device
    """

    def __init__(self, device: Device, **kwargs):
        """GetEsimDeviceOkResponse

        :param device: device
        :type device: Device
        """
        self.device = self._define_object(device, Device)
        self._kwargs = kwargs
