"""
blockchain.py

This is a connector to JSON based URL's such as blockchain.info
For now, the main usage of this file is to grab the utxo's for a
given address.
UTXO's (Unspent Transaction Outputs) are the record of transactions
for an address that haven't been spent yet.
"""
import urllib2
import json


class WebBlockchainInterface(object):
    """Abstract class for processing actual utxo's from a given web
    provider.
    """
    URL_TEMPLATE = None
    REVERSE_TXHASH = False

    def notify_confirmations(self, txhash, confirmations):
        pass

    def get_utxo(self, address):
        """Returns Unspent Transaction Outputs for a given address
        as an array of arrays. Each array in the array is a list of
        four elements that are necessary to initialize a UTXO object
        from utxodb.py
        """
        url = self.URL_TEMPLATE % address
        try:
            jsonData = urllib2.urlopen(url).read()
            data = json.loads(jsonData)
            utxos = []
            for utxo_data in data['unspent_outputs']:
                txhash = utxo_data['tx_hash']
                if self.REVERSE_TXHASH:
                    txhash = txhash.decode('hex')[::-1].encode('hex')
                if 'confirmations' in utxo_data:
                    self.notify_confirmations(txhash, utxo_data['confirmations'])
                utxo = [txhash, utxo_data['tx_output_n'],
                        utxo_data['value'], utxo_data['script']]
                utxos.append(utxo)
            return utxos
        except urllib2.HTTPError as e:
            if e.code == 500:         
                return []             
            raise                       # pragma: no cover

    def get_address_history(self, address):
        raise Exception('not implemented')


class BlockchainInfoInterface(WebBlockchainInterface):
    """Interface for blockchain.info. DO NOT USE FOR TESTNET!
    """
    URL_TEMPLATE = "https://blockchain.info/unspent?active=%s"
    REVERSE_TXHASH = True

    def __init__(self, coin_manager):
        self.coin_manager = coin_manager

    def notify_confirmations(self, txhash, confirmations):
        self.coin_manager.notify_confirmations(txhash, confirmations)

    def get_address_history(self, address):

        block_count = int(
            urllib2.urlopen("https://blockchain.info/q/getblockcount").read())        

        url = "https://blockchain.info/rawaddr/%s" % address
        jsonData = urllib2.urlopen(url).read()
        data = json.loads(jsonData)
        for tx in data['txs']:
            if 'block_height' in tx:
                confirmations = block_count - tx['block_height'] + 1
                self.notify_confirmations(tx['hash'], confirmations)
        return [tx['hash'] for tx in data['txs']]        


class AbeInterface(WebBlockchainInterface):
    """Interface for an Abe server, which is an open-source
    version of block explorer.
    See https://github.com/bitcoin-abe/bitcoin-abe for more information.
    """
    URL_TEMPLATE = "http://abe.bitcontracts.org/unspent/%s"

    def get_address_history(self, address):
        url = "http://abe.bitcontracts.org/unspent/%s" % address
        jsonData = urllib2.urlopen(url).read()
        data = json.loads(jsonData)
        return [tx['hash'] for tx in data['txs']]
