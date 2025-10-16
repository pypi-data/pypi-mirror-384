import pytest

from pyautd3_link_ethercrab import EtherCrab, EtherCrabOption, Status
from pyautd3_link_ethercrab.native_methods.autd3_capi_link_ethercrab import NativeMethods as NativeEtherCrab
from pyautd3_link_ethercrab.native_methods.autd3_capi_link_ethercrab import Status as Status_


def test_status():
    lost = Status.Lost()
    state_change = Status.StateChanged()
    err = Status.Error()
    resumed = Status.Resumed()

    assert lost == Status.Lost()
    assert state_change == Status.StateChanged()
    assert err == Status.Error()
    assert resumed == Status.Resumed()
    assert lost != state_change
    assert lost != err
    assert lost != Status_.Lost
    assert lost != resumed
    assert state_change != err
    assert state_change != lost
    assert state_change != Status_.StateChanged
    assert state_change != resumed
    assert err != lost
    assert err != state_change
    assert err != Status_.Error
    assert err != resumed
    assert resumed != lost
    assert resumed != state_change
    assert resumed != err
    assert resumed != Status_.Resumed

    status = Status.__private_new__(Status_.Lost, "lost")
    assert status == Status.Lost()
    assert str(status) == "lost"

    with pytest.raises(NotImplementedError):
        _ = Status()


def test_ethercrab_is_default():
    assert NativeEtherCrab().link_ether_crab_is_default(EtherCrabOption()._inner())


def test_ethercrab():
    def err_handler(dev: int, status: Status) -> None:
        print(f"Device[{dev}], status: {status}")

    _ = EtherCrab(err_handler, EtherCrabOption())
