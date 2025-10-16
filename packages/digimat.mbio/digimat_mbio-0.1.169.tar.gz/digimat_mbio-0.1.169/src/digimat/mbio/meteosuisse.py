#!/bin/python

from .task import MBIOTask
from .xmlconfig import XMLConfig

import requests
import io
import csv

# https://data.geo.admin.ch/ch.meteoschweiz.messwerte-aktuell/VQHA80.csv
# https://data.geo.admin.ch/ch.meteoschweiz.messwerte-aktuell/info/VQHA80_fr.txt

# tre200s0     °C             température de l'air à 2 m du sol; valeur instantanée
# rre150z0     mm             précipitation: sommation sur 10 minutes
# sre000z0     min            durée d'ensoleillement; sommation sur 10 minutes
# gre000z0     W/m²           rayonnement global; moyenne sur 10 minutes
# ure200s0     %              humidité de l'air relative à 2 m su sol; valeur instantanée
# tde200s0     °C             point de rosée à 2 m du sol; valeur instantanée
# dkl010z0     °              direction du vent; moyenne sur 10 minutes
# fu3010z0     km/h           vitesse du vent; moyenne sur 10 minutes
# fu3010z1     km/h           rafale (intégration 1 s); maximum
# prestas0     hPa            pression atmosphérique à l'altitude de la station (QFE); valeur instantanée
# pp0qffs0     hPa            pression atmosphérique réduite au niveau de la mer (QFF); valeur instantanée
# pp0qnhs0     hPa            pression atmosphérique réduite avec l'atmosphère standard (QNH); valeur instantanée
# ppz850s0     gpm            altitude géopotentielle de la surface de 850 hPa; valeur instantanée
# ppz700s0     gpm            altitude géopotentielle de la surface de 700 hPa; valeur instantanée
# dv1towz0     °              direction du vent vectorielle; instrument 1; moyenne sur 10 minutes
# fu3towz0     km/h           vitesse du vent, tour; moyenne sur 10 minutes
# fu3towz1     km/h           rafale (intégration 1 s), tour; maximum
# ta1tows0     °C             température de l'air instrument 1
# uretows0     %              humidité de l'air relative tour; valeur instantanée
# tdetows0     °C             point de rosée, tour


class MBIOTaskMeteoSuisse(MBIOTask):
    def initName(self):
        return 'weather'

    def onInit(self):
        self._timeoutRefresh=0
        self._retry=3
        self._stations={}

    def onLoad(self, xml: XMLConfig):
        self.valueDigital('comerr', default=False)

        items=xml.children('station')
        if items:
            for item in items:
                name=item.get('name')
                if name and not self._stations.get(name):
                    data={}
                    data['t']=self.value('%s_t' % name, unit='C', resolution=0.1)
                    data['r']=self.value('%s_r' % name, unit='W/m2', resolution=1)
                    data['hr']=self.value('%s_hr' % name, unit='%', resolution=1)
                    data['dewp']=self.value('%s_dewp' % name, unit='C', resolution=0.1)
                    data['wind']=self.value('%s_wind' % name, unit='ms', resolution=0.1)
                    data['rain']=self.value('%s_rain' % name, unit='mm', resolution=0.1)
                    self._stations[name.lower()]=data

    def poweron(self):
        return True

    def poweroff(self):
        return True

    def url(self):
        return 'https://data.geo.admin.ch/ch.meteoschweiz.messwerte-aktuell/VQHA80.csv'

    def decodeValueFloat(self, value, data, datakey, factor=1.0):
        if value is not None and data:
            try:
                v=data[datakey]
                if v and v!='-':
                    v=float(v)*factor
                    value.updateValue(v)
                    value.setError(False)
                    return True
            except:
                pass
            value.setError(True)
            return False

    def run(self):
        if self.isTimeout(self._timeoutRefresh):
            self._timeoutRefresh=self.timeout(60)
            error=False

            try:
                url=self.url()
                self.logger.debug('%s(%s)' % (self.__class__.__name__, url))
                # keep proxies (internet usage)
                r=requests.get(self.url(), timeout=5)
                if r and r.ok:
                    # self.logger.debug(r.text)
                    f=io.StringIO(r.text)
                    reader=csv.reader(f, delimiter=';')
                    headers=[]
                    for row in reader:
                        if not headers:
                            headers.extend(row)
                            continue

                        station=self._stations.get(row[0].lower())
                        if station:
                            data={}
                            for n in range(2, len(headers)):
                                data[headers[n].lower()]=row[n]

                            if not self.decodeValueFloat(station['t'], data, 'tre200s0'):
                                error=True

                            if not self.decodeValueFloat(station['r'], data, 'gre000z0'):
                                error=True

                            if not self.decodeValueFloat(station['hr'], data, 'ure200s0'):
                                error=True

                            if not self.decodeValueFloat(station['dewp'], data, 'tde200s0'):
                                error=True

                            if not self.decodeValueFloat(station['wind'], data, 'fu3010z0', 1.0/3.6):
                                error=True

                            if not self.decodeValueFloat(station['rain'], data, 'rre150z0'):
                                error=True
                else:
                    error=True
                    self.logger.error('%s(%s)' % (self.__class__.__name__, url))

            except:
                # self.logger.exception('meteo')
                error=True

            if not error:
                self._timeoutRefresh=self.timeout(60*10)
                self._retry=3
                self.values.comerr.updateValue(False)
            else:
                self._timeoutRefresh=self.timeout(60)
                if self._retry>0:
                    self._retry-=1
                    if self._retry==0:
                        self.values.comerr.updateValue(True)
                        for station in self._stations.keys():
                            for value in self._stations[station].values():
                                value.setError(True)

        return 5.0


if __name__ == "__main__":
    pass
