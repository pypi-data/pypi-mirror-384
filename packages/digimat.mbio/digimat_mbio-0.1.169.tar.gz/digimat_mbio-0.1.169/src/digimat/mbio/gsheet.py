#!/bin/python

import random
import string
import re
import time
import os
import json
import gspread
from google.oauth2.service_account import Credentials

from .task import MBIOTask
from .xmlconfig import XMLConfig


# Principe de base gspread API
# ----------------------------
# https://console.cloud.google.com/
# Créer un projet
# Dans les API, activer l'API "Google Sheets API"
# Dans les Identifiants, créer un "compte de service"
# Dans le compte de service, sous "clés" ajouter une clé JSON (récupérer le fichier auth .json)
# Récupérer l'email du compte de service (disponible dans le fichier .json) et partager la feuille Google Sheet avec cette adresse
# Récupérer l'id de la sheet (dispo dans l'URL) pour utilisation comme paramètre key dans l'appel .spreadsheet(key=xxx)

# gs=GSheet('digimat-mbio-gapi.json')
# sheets=gs.spreadsheet('1plgD2LxWK5S6obV9ZUHPdwbSKEvCyhxj8h01FDT0h-M')
# sheet=sheets.get_worksheet(0)
# print(sheet.acell('a1').value)
# sheet.update_acell("A1", "HELLO")
# sheet.format("A1", {'textFormat': {'bold': True}})
# sheet.batch_get(["A1", "A5"])


class GSheet(object):
    def __init__(self, fname='digimat-mbio-gapi.json', readonly=False, timeout=15.0):
        self._fname=fname
        self._readonly=readonly
        self._timeout=timeout
        self._client=None
        self._timeoutApi=0
        self._bufferWrite={}

        self._spreadsheet=None
        self._idspreadsheet=None
        self._worksheets=None
        self._worksheetsById=None
        self._worksheetsByIndex=None
        self._worksheetsByName=None
        self.resetCache()

    def resetCache(self):
        self._worksheets=[]
        self._worksheetsById={}
        self._worksheetsByIndex={}
        self._worksheetsByName={}

    def worksheet(self, key=0) -> gspread.worksheet.Worksheet:
        if self._spreadsheet and self._worksheets:
            try:
                return self._worksheetsById[key]
            except:
                pass
            try:
                return self._worksheetsByIndex[key]
            except:
                pass
            try:
                return self._worksheetsByName[key.lower()]
            except:
                pass
            try:
                # "sheet!a1"
                name=key.split('!')[0]
                return self._worksheetsByName[name.lower()]
            except:
                pass

        return None

    def apiSleep(self, n=0):
        wait=(2 ** n) + random.random()
        time.sleep(wait)

    # Warning: returns None is a sheetname doesn't exists
    def batchget(self, addresses, retries=5):
        for n in range(retries):
            try:
                data={}
                spreadsheet=self.spreadsheet()
                r=spreadsheet.values_batch_get(addresses)['valueRanges']
                for item in r:
                    # address is something like "sheet!a1"
                    # or "mydata" in case of a named field
                    address=item['range'].lower()
                    address=address.replace("'", "")
                    values=item.get('values')
                    if values is not None:
                        value=item['values'][0][0]
                    else:
                        value=None
                    data[address]=value
                return data
            except gspread.exceptions.APIError as e:
                if "429" in str(e):
                    self.apiSleep(n)
            except:
                break
        return None

    def get(self, sheetname: str, addresses, retries=5):
        for n in range(retries):
            try:
                worksheet=self.worksheet(sheetname)
                return worksheet.batch_get(addresses)
            except gspread.exceptions.APIError as e:
                if "429" in str(e):
                    self.apiSleep(n)
            except:
                break
        return None

    def batchset(self, data, retries=5):
        for n in range(retries):
            try:
                spreadsheet=self.spreadsheet()
                body={'value_input_option': 'USER_ENTERED', 'data': data}
                spreadsheet.values_batch_update(body)
                return True
            except gspread.exceptions.APIError as e:
                if "429" in str(e):
                    self.apiSleep(n)
            except:
                pass
        return False

    def resetBufferedWrite(self):
        self._bufferWrite={}

    def isBufferedWrite(self):
        if self._bufferWrite:
            return True
        return False

    def bufferedWrite(self, address, value) -> bool:
        if self._bufferWrite is None:
            self._bufferWrite={}

        if address and value is not None:
            address=address.strip()
            if '!' in address:
                sheetname=address.split('!')[0]
                if not self.worksheet(sheetname):
                    return False
            self._bufferWrite[address]=value
            return True
        return False

    def commit(self):
        if self.isBufferedWrite():
            data=[]
            for address in self._bufferWrite.keys():
                value=self._bufferWrite[address]
                if isinstance(value, (list, tuple)):
                    data.append({'range': address, 'values': [value]})
                else:
                    data.append({'range': address, 'values': [[value]]})

            result=self.batchset(data)
            self.resetBufferedWrite()
            return result
        return True

    def set(self, sheetname: str, data, retries=5):
        for n in range(retries):
            try:
                worksheet=self.sheet(sheetname)
                worksheet.batch_update(data)
                return True
            except gspread.exceptions.APIError as e:
                if "429" in str(e):
                    self.apiSleep(n)
            except:
                pass
        return False

    def __getitem__(self, key):
        return self.worksheet(key)

    def addWorksheet(self, worksheet: gspread.worksheet.Worksheet) -> gspread.worksheet.Worksheet:
        if worksheet:
            try:
                sid=worksheet.id
                if not self.worksheet(sid):
                    self._worksheets.append(worksheet)
                    self._worksheetsById[sid]=worksheet
                    self._worksheetsByIndex[worksheet.index]=worksheet
                    self._worksheetsByName[worksheet.title.lower()]=worksheet
            except:
                self.logger.exception('x')
                pass
        return worksheet

    def retrieveWorksheets(self):
        self.resetCache()
        if self._spreadsheet:
            try:
                worksheets=self._spreadsheet.worksheets()
                if worksheets:
                    for worksheet in worksheets:
                        self.addWorksheet(worksheet)
            except:
                self.logger.exception('x')
                pass
        return self._worksheets

    def client(self) -> gspread.client.Client:
        if self._client:
            return self._client

        scope='https://www.googleapis.com/auth/spreadsheets'
        if self._readonly:
            scope+='.readonly'

        try:
            credentials=Credentials.from_service_account_file(self._fname, scopes=[scope])
            if credentials:
                client=gspread.authorize(credentials)
                if client:
                    client.set_timeout(self._timeout)
                    self._client=client
                    self._spreadsheet=None
                    self.resetCache()
        except:
            pass

        return self._client

    def auth(self):
        client=self.client()
        if client is not None:
            return True
        return False

    def reauth(self) -> gspread.client.Client:
        self._client=None
        self._spreadsheet=None
        self.resetCache()
        if self.auth():
            if self._idspreadsheet:
                self.spreadsheet(self._idspreadsheet)
            return self._client
        return None

    def spreadsheet(self, key=None) -> gspread.Spreadsheet:
        try:
            if key:
                if self._spreadsheet and self._spreadsheet.id==key:
                    return self._spreadsheet

                client=self.client()
                if client:
                    if 'https://' in key:
                        spreadsheet=client.open_by_url(key)
                    else:
                        spreadsheet=client.open_by_key(key)

                    if spreadsheet:
                        self._spreadsheet=spreadsheet
                        self._idspreadsheet=key
                        self.retrieveWorksheets()
                pass
        except:
            pass

        return self._spreadsheet

    def cell(self, worksheet: gspread.worksheet.Worksheet, address) -> gspread.cell.Cell:
        try:
            if worksheet and address:
                return worksheet.acell(address)
        except:
            pass

    def __repr__(self):
        try:
            return '%s(%s, %d sheets)' % (self.__class__.__name__, self._spreadsheet.title, len(self._worksheets))
        except:
            pass
        if self._worksheets:
            return '%s(%s)' % (self.__class__.__name__, len(self._worksheets))
        return '%s()' % (self.__class__.__name__)


class MBIOTaskGSheet(MBIOTask):
    def initName(self):
        return 'gs'

    def onInit(self):
        self.config.set('credentials', 'digimat-mbio-gapi.json')
        self.config.set('readonly', False)
        self.config.set('refreshperiod', 10)
        self.config.set('timeout', 10)
        self.config.set('id')
        self._timeoutRefresh=0
        self._timeoutCommit=0
        self._timeoutRefreshNamedRanges=0
        self._sheets={}
        self._cells={}
        self._addresses={}
        self._namedRanges={}
        self._gsheet=None

    # Each sheet/cell must have a unique name (value name)
    def cell(self, name):
        name=name.lower()
        cell=self._cells.get(name)
        if cell:
            return cell
        return None

    def isA1Notation(self, address: str) -> bool:
        if address:
            return re.fullmatch(r"[A-Z]{1,3}+[1-9][0-9]*", address, re.IGNORECASE) is not None
        return False

    def normalizeAddress(self, sheet, address) -> str:
        if sheet and address:
            address=self.addressFromNamedRange(address)
            # allows for sheet!a1 notation or pure named field single string
            if address is not None:
                if self.isA1Notation(address):
                    address="%s!%s"  % (sheet['name'], address)
                address=address.lower()
        return address

    def addressFromNamedRange(self, name):
        try:
            address=self._namedRanges[name.lower()]
            if address is not None:
                return address
        except:
            pass
        return name

    def worksheetFromAddress(self, address) -> gspread.worksheet.Worksheet:
        gs=self.gsheet()
        address=self.addressFromNamedRange(address)
        return gs.worksheet(address)

    def declareAddress(self, sheet, address):
        self.logger.warning("DECLARE %s" % address)
        address=self.normalizeAddress(sheet, address)
        self.logger.warning("  normalized to %s" % address)
        if address and not address in self._addresses:
                self._addresses[address]=None
        return address

    def getAdressValue(self, sheet, address):
        address=self.normalizeAddress(sheet, address)
        return self._addresses.get(address)

    def loadCell(self, sheet, xml: XMLConfig, writable=True, digital=False, variables=None):
        if sheet:
            name=xml.get('name')
            name=self.replaceVariables(name, variables)
            vname='%s_%s' % (sheet['alias'], name)

            address=xml.get('cell') or xml.get('address')
            address=self.replaceVariables(address, variables)

            if name and not self.cell(vname) and address:
                xaddress=self.declareAddress(sheet, address)
                retain=False
                storeunit=False
                if writable:
                    storeunit=xml.getBool('storeunit')
                else:
                    retain=xml.getBool('retain', True)

                default=xml.getFloat('default')
                if digital:
                    value=self.valueDigital(vname, writable=writable, default=default, commissionable=True)
                else:
                    unit=xml.get('unit')
                    resolution=xml.getFloat('resolution', 0.1)
                    value=self.value(vname, unit=unit, resolution=resolution, writable=writable, default=default, commissionable=True)

                if retain:
                    try:
                        v=self.pickleRead('%s-cell-retain' % vname)
                        if v is not None:
                            value.updateValue(v)
                    except:
                        pass

                data={'name': vname, 'sheet': sheet['name'],
                      'address': address, 'xaddress': xaddress,
                      'writable': writable, 'retain': retain,
                      'value': value}

                if writable:
                    self._sheets[sheet['name']]['writablecells'].append(vname)
                    data['storeunit']=storeunit
                    # support for value expression calculations
                    self.loadValueExpression(value, xml, variables)

                self.logger.debug('Declaring GSheet(%s) CELL %s' % (self.name, vname))
                self._cells[vname]=data
                self._sheets[sheet['name']]['cells'].append(vname)

                return data
        return None

    def loadSheet(self, name, xml: XMLConfig):
        if name:
            name=name.strip()
        sheet=self._sheets.get(name)
        if xml is not None and sheet is None:
            alias=xml.get('alias', name)
            self.logger.info('Declaring GSheet(%s) SHEET %s (alias %s)' % (self.name, name, alias))
            sheet={'name': name, 'alias': alias, 'cells': [], 'writablecells': [], 'dumps': [], 'imports': [], 'exports': []}
            self._sheets[name]=sheet

            myvariables={'gsheet': self.name,
                         'sheetname': sheet['name'], 'name': sheet['name'],
                         'sheetalias': sheet['alias'], 'alias': sheet['alias']}

            items=xml.children('ai')
            if items:
                for item in items:
                    self.loadCell(sheet, item, writable=False, digital=False, variables=myvariables)
            items=xml.children('di')
            if items:
                for item in items:
                    self.loadCell(sheet, item, writable=False, digital=True, variables=myvariables)
            items=xml.children('ao')
            if items:
                for item in items:
                    self.loadCell(sheet, item, writable=True, digital=False, variables=myvariables)
            items=xml.children('do')
            if items:
                for item in items:
                    self.loadCell(sheet, item, writable=True, digital=True, variables=myvariables)

            items=xml.children('dump')
            if items:
                for item in items:
                    cell=item.get('cell')
                    cell=self.replaceVariables(cell, myvariables)
                    key=item.get('key')
                    key=self.replaceVariables(key, myvariables)
                    if cell and key:
                        refresh=item.getInt('refresh', 15, vmin=5)
                        data={'cell': cell, 'key': key, 'refresh': refresh, 'timeout': 0}
                        self.logger.info('Declaring GSheet(%s) SHEET %s (alias %s) DUMP [%s]->%s' % (self.name, name, alias, key, cell))
                        sheet['dumps'].append(data)

            items=xml.children('import')
            if items:
                for item in items:
                    cell=item.get('cell')
                    key=item.get('key')
                    key=self.replaceVariables(key, myvariables)
                    if cell and key:
                        xaddress=self.declareAddress(sheet, cell)
                        data={'cell': cell, 'xaddress': xaddress, 'key': key}
                        self.logger.info('Declaring GSheet(%s) SHEET %s (alias %s) IMPORT %s->%s' % (self.name, name, alias, cell, key))
                        sheet['imports'].append(data)

            items=xml.children('export')
            if items:
                for item in items:
                    key=item.get('key')
                    key=self.replaceVariables(key, myvariables)
                    cell=item.get('cell')
                    if key and cell:
                        xaddress=self.declareAddress(sheet, cell)
                        storeunit=item.getBool('storeunit', False)
                        data={'key': key, 'cell': cell, 'xaddress': xaddress, 'storeunit': storeunit}
                        self.logger.info('Declaring GSheet(%s) SHEET %s (alias %s) EXPORT %s->%s' % (self.name, name, alias, key, cell))
                        sheet['exports'].append(data)

    def onLoad(self, xml: XMLConfig):
        self.config.update('credentials', xml.get('credentials'))
        self.config.update('readonly', xml.getBool('readonly'))
        self.config.update('refreshperiod', xml.getInt('refresh'))
        self.config.update('timeout', xml.getInt('timeout', vmin=3))
        self.config.update('id', xml.get('id'))
        if not self.config.id:
            self.config.update('id', self.pickleRead('id'))
        self.pickleWrite('id', self.config.id)

        # Remember that we are not online in this step !

        items=xml.children('sheet')
        if items:
            for item in items:
                names=item.get('name', 0).split(',')
                for name in names:
                    self.loadSheet(name, item)

    def credentials(self):
        fname=os.path.join(self.getMBIO().rootPath() or '.', self.config.credentials)
        fname=os.path.expanduser(fname)

        if not os.path.exists(fname):
            fname=os.path.join('/etc/sysconfig/digimat/credentials', self.config.credentials)

        if os.path.exists(fname):
            return fname

    def loadCredentialsData(self):
        fname=self.credentials()
        try:
            with open(fname) as f:
                data = json.load(f)
                return data
        except:
            pass

    def retrieveCredentialsServiceEmail(self):
        data=self.loadCredentialsData()
        try:
            return data['client_email']
        except:
            pass

    def gsheet(self, reset=False) -> GSheet:
        if reset or not self._gsheet:
            fname=self.credentials()
            if fname:
                self.logger.debug('Using GSheet(%s) credentials %s' % (self.name, fname))
                gs=GSheet(fname, readonly=self.config.readonly, timeout=self.config.timeout)
                self._gsheet=gs

        return self._gsheet

    def poweron(self):
        self.logger.info('Retrieving GSheet(%s)' % (self.name))
        gs=self.gsheet(True)
        if gs:
            spreadsheet=gs.spreadsheet(self.config.id)
            if spreadsheet:
                self.logger.debug('Connected to GSheet(%s) %s' % (self.name, gs))
                return True

        self.logger.error('Unable to retrieve GSheet(%s)' % (self.name))
        return False

    def poweroff(self):
        self._gsheet=None
        return True

    def str2value(self, data):
        try:
            data=data.upper().replace(',', '.')
            if data=='TRUE':
                v=1.0
            elif data=='FALSE':
                v=0.0
            else:
                v=float(data)
            return v
        except:
            pass
        return None


    def gridRangeToCellAddress(self, worksheet: gspread.worksheet.Worksheet, gr):
        try:
            # sheetId is implicitely 0 if not specified!
            sC = gr.get("startColumnIndex")
            sR = gr.get("startRowIndex")
            eC = gr.get("endColumnIndex")
            eR = gr.get("endRowIndex")

            if sR is None or sC is None:
                return None

            if eR is None: eR = sR + 1
            if eC is None: eC = sC + 1

            # range indexes are 0 based, while row/col addresses are 1 based
            def cellAddress(r0, c0):
                return self.rowcol_to_a1(r0+1, c0+1).lower()

            start = cellAddress(sR, sC)
            end   = cellAddress(eR - 1, eC - 1)
            if start == end:
                return f"{worksheet.title}!{start}"
        except:
            self.logger.exception('x')
            pass
        return None

    def retrieveNamedRanges(self):
        self.logger.debug('Reloading GSheet(%s) named ranges' % self.name)
        self._timeoutRefreshNamedRanges=self.timeout(180)

        gs=self.gsheet()
        gs.retrieveWorksheets()
        spreadsheet=gs.spreadsheet()
        items=spreadsheet.list_named_ranges()
        # self.logger.warning(items)

        if items:
            self._namedRanges={}
            try:
                for nr in items:
                    name=nr.get('name').lower()
                    gr=nr.get('range')
                    # sheetId is 0 if not given
                    sid=gr.get('sheetId', 0)
                    worksheet=gs.worksheet(sid)
                    address=self.gridRangeToCellAddress(worksheet, gr)
                    if name and address:
                        self._namedRanges[name]=address.lower()

                self._timeoutRefreshNamedRanges=self.timeout(60)
            except:
                self.logger.exception('x')
                pass

    def sheetImportManager(self, sheet) -> bool:
        result=True

        for item in sheet['imports']:
            v=self.getAdressValue(sheet, item['cell'])
            value=self.getMBIO().value(item['key'])
            # self.logger.warning("IMPORT %s-->%s" % (v, value))

            if value is not None:
                if v is not None:
                    value.manual(v)
                else:
                    value.auto()
                continue

        return result

    def a1_to_rowcol(self, address):
        if address:
            try:
                address=self.addressFromNamedRange(address)
                if '!' in address:
                    address=address.split('!')[1]
                row,col=gspread.utils.a1_to_rowcol(address)
                return row, col
            except:
                pass
        return None

    def rowcol_to_a1(self, row, col):
        try:
            return gspread.utils.rowcol_to_a1(row, col)
        except:
            pass

    def sheetExportManager(self, sheet):
        gs=self.gsheet()

        if not gs.worksheet(sheet['name']):
            self.logger.debug('GSheet(%s) ignore offline sheet %s EXPORTs' % (self.name, sheet['name']))
            return

        # EXPORTS (key->cell maping without using mbio values)
        for export in sheet['exports']:
            self.microsleep()
            address=self.addressFromNamedRange(export['xaddress'])
            key=export['key']
            value=self.getMBIO().value(key)
            if value is not None and value.value is not None:
                v=self.getAdressValue(sheet, export['cell'])
                if v is None or value.checkIfValueWillTriggerNotify(v):
                    self.logger.debug('GSheet(%s) EXPORT %s->%s (%s)' % (self.name, value, address, v))
                    data=[value.value]
                    if export['storeunit']:
                        data.append(value.unitstr())
                    gs.bufferedWrite(address, data)

    def sheetSyncManager(self, sheet):
        gs=self.gsheet()

        # collect all cells with pending sync
        cells=sheet['writablecells']

        # AO, DO
        for name in cells:
            self.microsleep()
            cell=self.cell(name)
            value=cell['value']

            if value.isPendingSync():
                address=self.addressFromNamedRange(cell['xaddress'])
                data=[value.toReachValue]
                if cell['storeunit']:
                    data.append(value.unitstr())
                if gs.bufferedWrite(address, data):
                    value.setError(False)
                else:
                    value.setError(True)
                value.clearSync()

    def sheetDumpManager(self, sheet):
        gs=self.gsheet()
        for dump in sheet['dumps']:
            self.microsleep()
            if not self.isTimeout(dump['timeout']):
                continue

            values=self.getMBIO().values(dump['key'])
            address=self.normalizeAddress(sheet, dump['cell'])
            self.logger.debug('Dumping %s(%s) from GSheet(%s) to %s' % (sheet['name'], dump['key'], self.name, address))
            row,col=self.a1_to_rowcol(address)
            if values:
                for value in values:
                    iotag=''
                    if value.config.iomaptag:
                        iotag=value.config.iomaptag

                    gs.bufferedWrite(address, [value.key, iotag, value.value, value.unitstr(), value.flags])
                    row+=1
                    address=self.rowcol_to_a1(row, col)
                    address=self.normalizeAddress(sheet, address)
                    dump['timeout']=self.timeout(dump['refresh'])

    def run(self):
        gs=self.gsheet()

        if self.isTimeout(self._timeoutRefreshNamedRanges):
            self.retrieveNamedRanges()
            self.logger.debug(self._namedRanges)

        # refresh spreadsheet cells values (read values from spreadsheet)
        if self.isTimeout(self._timeoutRefresh):
            self._timeoutRefresh=self.timeout(self.config.refreshperiod)

            if self._addresses:
                addresses=[]
                for address in self._addresses.keys():
                    # self.logger.debug(address)
                    address=self.addressFromNamedRange(address)

                    if address is None:
                        # self.logger.warning("IGNORE refresh for unknown address %s" % address)
                        continue

                    # WARNING!
                    # we have to avoid request a non existing sheet (batchget will globally fails and return nothing)
                    worksheet=self.worksheetFromAddress(address)
                    if worksheet is None:
                        self.logger.warning("GSheet(%s) IGNORE refresh address %s (OFFLINE)" % (self.name, address))
                        continue

                    addresses.append(address)

                if addresses:
                    self.logger.debug('Retrieve cells %s from GSheet(%s)' % (addresses, self.name))
                    data=gs.batchget(addresses)
                    # self.logger.debug(data)
                    if data:
                        self.logger.debug(data)
                        # reset values
                        for address in self._addresses:
                            self._addresses[address]=None

                        for address in data:
                            v=self.str2value(data[address])
                            self._addresses[address]=v

            # update values
            for cell in self._cells.values():
                address=self.addressFromNamedRange(cell['xaddress'])
                value=cell['value']

                v=self._addresses.get(address)
                if v is not None:
                    value.updateValue(v)
                    value.setError(False)
                    if cell['retain']:
                        self.pickleWrite('%s-cell-retain' % cell['name'], v)
                    continue

                value.setError(True)

        for sheet in self._sheets.values():
            self.microsleep()
            self.sheetImportManager(sheet)
            self.sheetDumpManager(sheet)
            self.sheetSyncManager(sheet)
            self.sheetExportManager(sheet)

        if self.isTimeout(self._timeoutCommit):
            if gs.isBufferedWrite():
                self.logger.info('Commit GSheet(%s) %s' % (self.name, gs._bufferWrite))
                if not gs.commit():
                    self.logger.error('Commit GSheet(%s) %s ERROR' % (self.name, gs._bufferWrite))

                self._timeoutCommit=self.timeout(5)

        return 5.0

    @property
    def sid(self):
        return self.config.id
