from dataclasses import dataclass

from agton.ton import Contract, MsgAddress, Cell, Slice, MessageRelaxed, CurrencyCollection
from agton.jetton.messages import JettonTransfer

@dataclass(frozen=True, slots=True)
class JettonWalletData:
    balance: int
    owner: MsgAddress
    jetton: MsgAddress
    jetton_wallet_code: Cell

class JettonWallet(Contract):
    def get_wallet_data(self) -> JettonWalletData:
        s = self.run_get_method('get_wallet_data')
        match s:
            case (
                int() as balance,
                Slice() as owner,
                Slice() as jetton,
                Cell() as jetton_wallet_code
            ):
                return JettonWalletData(
                    balance,
                    owner.load_msg_address(),
                    jetton.load_msg_address(),
                    jetton_wallet_code
                )
            case _:
                raise TypeError(f"Unexpected result for get_wallet_data: {s!r}")
    
    def create_jetton_transfer(self, *,
                               value: int | CurrencyCollection,
                               query_id: int,
                               amount: int,
                               destination: MsgAddress,
                               response_destination: MsgAddress,
                               custom_payload: Cell | None = None,
                               forward_amount: int = 0,
                               forward_payload: Cell = Cell.empty()) -> MessageRelaxed:
        body = JettonTransfer(
            query_id, amount, destination, response_destination,
            custom_payload, forward_amount, forward_payload
        )
        return self.create_internal_message(
            value=value,
            body=body.to_cell(),
        )
