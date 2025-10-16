import threading
from dataclasses import dataclass
from pathlib import Path

import pytest
import torch
import torch.multiprocessing as mp

from blazefl.core.client_trainer import IPCMode
from blazefl.core.utils import SHMHandle
from src.blazefl.core import ProcessPoolClientTrainer


@dataclass
class UplinkPackage:
    cid: int
    message: str
    tensor: torch.Tensor | SHMHandle


@dataclass
class DownlinkPackage:
    message: str


@dataclass
class ClientConfig:
    cid: int


class DummyProcessPoolClientTrainer(
    ProcessPoolClientTrainer[UplinkPackage, DownlinkPackage, ClientConfig]
):
    def __init__(
        self,
        num_parallels: int,
        share_dir: Path,
        device: str,
        ipc_mode: IPCMode,
    ):
        self.num_parallels = num_parallels
        self.share_dir = share_dir
        self.share_dir.mkdir(parents=True, exist_ok=True)
        self.device = device
        if self.device == "cuda":
            self.device_count = torch.cuda.device_count()
        self.cache: list[UplinkPackage] = []
        self.ipc_mode = ipc_mode
        self.manager = mp.Manager()
        self.stop_event = self.manager.Event()

    def uplink_package(self) -> list[UplinkPackage]:
        return self.cache

    def get_client_config(self, cid: int) -> ClientConfig:
        return ClientConfig(cid=cid)

    def prepare_uplink_package_buffer(self) -> UplinkPackage:
        return UplinkPackage(cid=-1, message="", tensor=torch.zeros(1))

    @staticmethod
    def worker(
        config: ClientConfig | Path,
        payload: DownlinkPackage | Path,
        device: str,
        stop_event: threading.Event,
        *,
        shm_buffer: UplinkPackage | None = None,
    ) -> UplinkPackage | Path:
        def _storage_worker(
            config_path: Path,
            payload_path: Path,
            device: str,
            stop_event: threading.Event,
        ) -> Path:
            config = torch.load(config_path, weights_only=False)
            assert isinstance(config, ClientConfig)
            payload = torch.load(payload_path, weights_only=False)
            dummy_uplink_package = _shared_memory_worker(
                config=config,
                payload=payload,
                device=device,
                stop_event=stop_event,
            )
            torch.save(dummy_uplink_package, config_path)
            return config_path

        def _shared_memory_worker(
            config: ClientConfig,
            payload: DownlinkPackage,
            device: str,
            stop_event: threading.Event,
        ) -> UplinkPackage:
            _ = stop_event
            _ = device
            dummy_uplink_package = UplinkPackage(
                cid=config.cid,
                tensor=torch.rand(1),
                message=payload.message + "<client_to_server>",
            )
            return dummy_uplink_package

        if isinstance(config, Path) and isinstance(payload, Path):
            return _storage_worker(config, payload, device, stop_event)
        elif isinstance(config, ClientConfig) and isinstance(payload, DownlinkPackage):
            package = _shared_memory_worker(config, payload, device, stop_event)
            assert shm_buffer is not None
            shm_buffer.tensor = package.tensor
            package.tensor = SHMHandle()
            return package
        else:
            raise TypeError(
                "Invalid types for config and payload."
                "Expected ClientConfig and DownlinkPackage or Path."
            )


@pytest.mark.parametrize("num_parallels", [1, 2, 4])
@pytest.mark.parametrize("cid_list", [[], [42], [0, 1, 2]])
@pytest.mark.parametrize("ipc_mode", ["storage", "shared_memory"])
def test_process_pool_client_trainer(
    tmp_path: Path,
    num_parallels: int,
    cid_list: list[int],
    ipc_mode: IPCMode,
) -> None:
    trainer = DummyProcessPoolClientTrainer(
        num_parallels=num_parallels,
        share_dir=tmp_path,
        device="cpu",
        ipc_mode=ipc_mode,
    )

    dummy_payload = DownlinkPackage(message="<server_to_client>")

    trainer.local_process(dummy_payload, cid_list)

    assert len(trainer.cache) == len(cid_list)
    for i, cid in enumerate(cid_list):
        result = trainer.cache[i]
        assert result.cid == cid
        assert result.message == "<server_to_client><client_to_server>"

    package = trainer.uplink_package()
    assert len(package) == len(cid_list)

    for i, cid in enumerate(cid_list):
        result = package[i]
        assert result.cid == cid
        assert result.message == "<server_to_client><client_to_server>"
