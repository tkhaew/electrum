from electrum.util import print_error
from urlparse import urlparse, parse_qs
from PyQt4.QtGui import QPushButton, QMessageBox, QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel
from PyQt4.QtCore import Qt

from electrum.i18n import _
from electrum.bitcoin import is_valid

import httplib, urllib
import json

from electrum import BasePlugin
class Plugin(BasePlugin):

    def fullname(self): return 'Mixer'

    def description(self): return "Mixer\n\nThis plugin integrates the blockchain.info coin mixer. It allows sending / receiving via a generated mixer address.\n\nBlockchain.info charges a 0.5% fee.\n\nCaution: Advanced users only."

    def __init__(self, gui, name):
        BasePlugin.__init__(self, gui, name)
        self._is_available = self._init()

    def _init(self):
        self.mix_addr = ""
        self.is_fee_hook = False
        return True

    def is_available(self):
        return self._is_available

    def create_send_tab(self, grid):
        b = QPushButton(_("Via Mixer"))
        b.clicked.connect(self.via_mixer)
        grid.addWidget(b, 2, 5)
        self.mix_fee = QLabel("")
        self.mix_fee.setAlignment(Qt.AlignCenter)
        grid.addWidget(self.mix_fee, 5, 3)
        
    def receive_menu(self, menu, addrs):
        menu.addAction(_("QR code, Via Mixer"), lambda: self.show_qrcode_via_mixer(addrs[0]) ) 
        
    def via_mixer(self):
        if not self.is_fee_hook:
            self.gui.main_window.amount_e.textChanged.connect(lambda: self.update_mix_fee() )
            self.gui.main_window.fee_e.textChanged.connect(lambda: self.update_mix_fee() ) 
            self.gui.main_window.payto_e.textChanged.connect(lambda: self.update_mix_fee() )
            self.is_fee_hook = True
        self.mix_addr = self.request_mixer_address(self.gui.main_window.payto_e.text())
        if is_valid(self.mix_addr):
            self.gui.main_window.payto_e.setText(self.mix_addr)
            self.update_mix_fee()

    def show_qrcode_via_mixer(self, addr):
        mix_addr = self.request_mixer_address(addr)
        if is_valid(mix_addr):
            self.gui.main_window.show_qrcode("bitcoin:" + mix_addr, _("Address") )
            self.update_mix_fee
            
    def update_mix_fee(self):
        if is_valid(self.mix_addr)  and  self.mix_addr == self.gui.main_window.payto_e.text():
            self.mix_fee.setText("(%s: %.8f)" % (_("Est. Mix Fee"), ((float(self.gui.main_window.amount_e.text())+float(self.gui.main_window.fee_e.text())) * 0.005 )) )
        else:
            self.mix_fee.setText("")

    def request_mixer_address(self, addr):
        try:
            params = urllib.urlencode( {"action": "create-mix", "address": addr, "shared": "true"} )
            headers = {"Content-type": "application/x-www-form-urlencoded; charset=UTF-8", "Accept": "application/json, text/javascript, */*; q=0.01"}
            connection = httplib.HTTPSConnection("blockchain.info")
            connection.request("POST", "/forwarder", params, headers)
        except:
            self.gui.main_window.show_message("Could not connect to blockchain.info mixer")
            return ""
            
        response = connection.getresponse()
        if response.reason == httplib.responses[httplib.NOT_FOUND]:
            self.gui.main_window.show_message("No reponse from blockchain.info mixer")
            return ""
        try:
            response = json.loads(response.read())
        except:
            self.gui.main_window.show_message("Invalid response to blockchain.info mixer")
            return ""
            
        msg = "Payment to %s\nForwards to %s\n\nMax 250 btc, Min 0.2btc, Fee %s%%\n\nValid for 8 hours or one 6 confirmation transaction (which ever comes first) after which all records will be removed from mixer logs.\n\n Do you want to use mixer address?" % (response['input_address'], response['destination'], response['fee_percent'])
        return response['input_address'] if self.gui.main_window.question(msg) else addr

    

    
    

