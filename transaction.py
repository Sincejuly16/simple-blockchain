# coding:utf-8
import hashlib
import json
from binascii import hexlify
import util
from script import OP_DUP, OP_HASH160, Script, OP_EQUALVERIFY, OP_CHECKSIG
from wallet import Wallet

"""
定义了交易，输入，输出及其验证方法
"""


class Transaction:
    def __init__(self, txins, txouts, timestamp):
        """
        :param txins: 从其他账户输入的交易
        :param txouts: 向其他账户输出的交易
        """
        self.txins = txins
        self.txouts = txouts
        self.timestamp = timestamp
        self.txid = self.get_txid()

    def get_txid(self):
        """
        TODO 根据交易时间戳，输入和输出的交易数组生成唯一标识这笔交易的id
        """
        value = str(self.timestamp) + ",".join(str(txin) for txin in self.txins) + ",".join(
            str(txout) for txout in self.txouts)
        sha = hashlib.sha256(value.encode('utf-8'))
        return str(sha.hexdigest())

    def get_hash(self):
        """
        :return 这笔交易对应的哈希摘要
        """
        sha = hashlib.sha256(self.__str__().encode())
        return sha.hexdigest()

    def is_coinbase(self):
        """
        检测这笔交易是否来自挖矿，
        挖矿产生的coinbase不存在输入，txins为None
        """
        return self.txins[0].prev_txid is None

    def json_output(self):
        output = {
            'txid': self.txid,
            'timestamp': self.timestamp,
            'txins': [txin.json_output() for txin in self.txins],
            'txouts': [txout.json_output() for txout in self.txouts]
        }
        return output

    def __str__(self):
        return json.dumps(self.json_output(), default=lambda obj: obj.__dict__, sort_keys=True, indent=4)


class TxInput:
    """
    一个输入引用之前的一个输出
    """

    def __init__(self, prev_txid, out_idx, signature, pubkey):
        """
        :param prev_txid: 指向之前的交易id
        :param out_idx: 存储上一笔交易中所引用输出的索引
        :param signature: signature是一个脚本，提供了可解锁输出结构里面ScriptPubKey字段的数据（实际就是确认这个输出中公钥对应的私钥持有者是否本人）。
        """
        self.prev_txid = prev_txid
        self.prev_tx_out_idx = out_idx
        self.signature = signature
        self.pubkey = pubkey

    def can_unlock_txoutput_with(self, address):
        """
        检测这个地址是否是这笔输出的目标地址
        :param address:
        :return:
        """
        return Wallet.get_address(self.pubkey) == address

    def json_output(self):
        """
        TODO 生成json对象
        :return:
        """
        output = {
            'prev_txid': self.prev_txid,
            'prev_tx_out_idx': self.prev_tx_out_idx,
            'signature': util.get_hash(self.signature) if self.signature is not None else "",
            'pubkey_hash': Script.sha160(str(self.pubkey)) if self.pubkey is not None else ""
        }
        return output

    def __str__(self):
        return json.dumps(self.json_output(), default=lambda obj: obj.__dict__, sort_keys=True, indent=4)


class TxOutput:
    """
    货币存储在TxOutput中，一个用户钱包的余额相当于某个地址下未使用过的TxOutput中value之和
    """

    def __init__(self, value, pubkey_hash):
        """
        锁定脚本会把输出锁在一个特定的比特币地址上，从而把一定数量的比特币的所有权转移到新的所有者上。
        :param value: 一定量的货币
        :param pubkey_hash: <str>，锁定脚本，要使用这个输出，必须要解锁该脚本。pubkey_hash=sha256(ripemd160(pubkey))
        """
        self.value = value
        self.pubkey_hash = pubkey_hash
        self.scriptPubKey = None

        self.lock(pubkey_hash)

    def get_script_pubkey(self):
        return self.scriptPubKey

    def can_be_unlocked_with(self, address):
        """
        判断当前输出，address钱包地址是否可用
        :param address: <str>钱包地址
        :return:
        """
        return self.pubkey_hash == hexlify(Wallet.b58decode(address)).decode('utf-8')

    def lock(self, pubkey_hash):
        """
        锁定输出交易，对输出进行加密，只有pubkey本人才能使用，锁定脚本是一个操作序列，使用一个栈模拟函数调用(参考bit_cash的实现)
        :param pubkey_hash: 要使用这个输出，使用者必须证明他拥有这笔交易。pubkey_hash=sha256(ripemd160(pubkey))
        :return:
        """
        self.scriptPubKey = [OP_DUP, OP_HASH160, pubkey_hash, OP_EQUALVERIFY, OP_CHECKSIG]

    def __str__(self):
        return json.dumps(self.json_output(), default=lambda obj: obj.__dict__, sort_keys=True, indent=4)

    @staticmethod
    def get_opcode_name(opcode):
        if opcode == OP_DUP:
            return "OP_DUP"
        if opcode == OP_HASH160:
            return "OP_HASH160"
        if opcode == OP_EQUALVERIFY:
            return "OP_EQUALVERIFY"
        if opcode == OP_CHECKSIG:
            return "OP_CHECKSIG"
        return opcode

    def json_output(self):
        """
        TODO 生成json对象
        :return:
        """
        output = {
            'value': self.value,
            'script_pubkey': [self.get_opcode_name(opcode) for opcode in self.scriptPubKey]
        }
        return output
