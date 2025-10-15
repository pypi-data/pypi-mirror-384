from dataclasses import dataclass

from agton.ton import Contract, MsgAddress, MsgAddressInt, Cell, Slice, MessageRelaxed, CurrencyCollection
from agton.jetton.messages import JettonTransfer

from .jetton_wallet import JettonWallet

@dataclass(frozen=True, slots=True)
class JettonMasterData:
    total_supply: int 
    mintable: int 
    admin_address: MsgAddressInt
    jetton_content: Cell
    jetton_wallet_code: Cell

class JettonMaster(Contract):
    def get_jetton_data(self) -> JettonMasterData:
        s = self.run_get_method('get_jetton_data')
        match s:
            case (
                int() as total_supply,
                int() as mintable,
                Slice() as admin_address,
                Cell() as jetton_content,
                Cell() as jetton_wallet_code
            ):
                return JettonMasterData(
                    total_supply,
                    bool(mintable),
                    admin_address.load_msg_address_int(),
                    jetton_content,
                    jetton_wallet_code
                )
            case _:
                raise TypeError(f"Unexpected result for get_jetton_data: {s!r}")
    
    def get_wallet_address(self, owner: MsgAddressInt) -> MsgAddressInt:
        s = self.run_get_method('get_wallet_address', owner.to_slice())
        match s:
            case Slice():
                return s.load_msg_address_int()
            case Cell():
                return s.begin_parse().load_msg_address_int()
            case _:
                raise TypeError(f"Unexpected result for get_wallet_address: {s!r}")
    
    def get_jetton_wallet(self, owner: MsgAddressInt) -> JettonWallet:
        return JettonWallet(self.provider, self.get_wallet_address(owner))

    def create_jetton_transfer(self, *,
                                query_id: int,
                                amount: int,
                                destination: MsgAddress,
                                response_destination: MsgAddress,
                                custom_payload: Cell | None = None,
                                forward_amount: int = 0,
                                forward_payload: Cell = Cell.empty()) -> JettonTransfer:
        return JettonTransfer(query_id, amount, destination, response_destination,
                              custom_payload, forward_amount, forward_payload)
