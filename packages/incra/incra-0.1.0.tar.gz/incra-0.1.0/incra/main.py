"""
Módulo do INCRA
Para obter e atualizar dado.
"""

from datetime import datetime
from pathlib import Path
from typing import Literal
from urllib.parse import quote, urljoin
from zipfile import ZipFile

import geopandas as gpd

from incra.net import create_session


class INCRA:
    def __init__(
        self,
        layer: Literal[
            'Imóvel certificado SIGEF Total',
            'Imóvel certificado SIGEF Público',
            'Imóvel certificado SIGEF Privado',
            'Imóvel certificado SNCI Total',
            'Imóvel certificado SNCI Público',
            'Imóvel certificado SNCI Privado',
            'Projetos de Assentamento Total',
            'Projetos de Assentamento Federal',
            'Projetos de Assentamento Reconhecimento',
            'Áreas de Quilombolas',
        ],
        uf: Literal[
            'AC',
            'AL',
            'AP',
            'AM',
            'BA',
            'CE',
            'DF',
            'ES',
            'GO',
            'MA',
            'MT',
            'MS',
            'MG',
            'PA',
            'PB',
            'PR',
            'PE',
            'PI',
            'RJ',
            'RN',
            'RS',
            'RO',
            'RR',
            'SC',
            'SP',
            'SE',
            'TO',
            None,
        ] = None,
    ) -> None:
        dict_layers = {
            'Imóvel certificado SIGEF Total': {
                'filename': 'Sigef Brasil.zip',
                'dropdown': 'sigef',
            },
            'Imóvel certificado SIGEF Público': {
                'filename': 'Sigef Público.zip',
                'dropdown': 'sigef_pub',
            },
            'Imóvel certificado SIGEF Privado': {
                'filename': 'Sigef Privado.zip',
                'dropdown': 'sigef_pri',
            },
            'Imóvel certificado SNCI Total': {
                'filename': 'Imóvel certificado SNCI Brasil.zip',
                'dropdown': 'snci',
            },
            'Imóvel certificado SNCI Público': {
                'filename': 'Imóvel certificado SNCI Público.zip',
                'dropdown': 'snci_pub',
            },
            'Imóvel certificado SNCI Privado': {
                'filename': 'Imóvel certificado SNCI Privado.zip',
                'dropdown': 'snci_pri',
            },
            'Projetos de Assentamento Total': {
                'filename': 'Assentamento Brasil.zip',
                'dropdown': 'assent',
            },
            'Projetos de Assentamento Federal': {
                'filename': 'Assentamento Federal.zip',
                'dropdown': 'assent_f',
            },
            'Projetos de Assentamento Reconhecimento': {
                'filename': 'Assentamento Reconhecimento.zip',
                'dropdown': 'assent_r',
            },
            'Áreas de Quilombolas': {
                'filename': 'Áreas de Quilombolas.zip',
                'dropdown': 'quilom',
            },
        }
        # Parâmetro
        self.layer = layer
        self._filename = dict_layers[layer]['filename']
        self._dropdown = dict_layers[layer]['dropdown']
        self.uf = uf

        # Create Session
        self.session = create_session()

    @property
    def _uf_to_update(self) -> str:
        """
        Ajusta a UF para fazer o update dos dados

        :return: uf para inserir no `requests.post`
        :rtype: str
        """
        if self.uf is None:
            return ''
        else:
            return self.uf

    @property
    def _filename_to_download(self) -> str:
        """
        Ajusta o filename para fazer o download dos dados

        :return: filename para inserir no `requests.get`
        :rtype: str
        """

        # Estado
        if self.uf is not None:
            filename = self._filename.strip()
            filename = filename.removesuffix('.zip')
            filename = f'{filename}_{self.uf.upper()}.zip'
            return filename

        else:
            return self._filename

    def update(self):
        """
        Atualiza
        """

        # Faz o request para atualizar o dado
        s = self.session.post(
            url='https://certificacao.incra.gov.br/csv_shp/export_shp.py',
            params={
                'selectshp': self._dropdown,
                'selectuf': self._uf_to_update,
            },
            stream=True,
        )
        if s.status_code != 200:
            raise Exception(f'Não foi possível atualizar. {s.status_code}')

    def download(self, output_path) -> None:
        """
        Fazer o download 

        :param output_path: Pasta que irá receber os arquivos
        :type output_path: str | Path
        """
        url_lyr = urljoin(
            base='https://certificacao.incra.gov.br/csv_shp/zip/',
            url=quote(self._filename_to_download),
        )

        # Faz requisição
        s = self.session.get(url=url_lyr, stream=True)

        # Define nome do arquivo
        self.output_file = Path(output_path) / self._filename_to_download

        # Faz o request para obter o dado
        with open(file=self.output_file, mode='wb') as f:
            for chunk in s.iter_content(chunk_size=8192):
                if chunk:  # filtra keep-alive chunks
                    f.write(chunk)

        print(self.get_shp_datetime())

    def get_shp_datetime(self) -> datetime | None:
        """
        Obtem data do aquivo shapefile

        :return: Data do arquivo shapefile
        :rtype: datetime
        """

        with ZipFile(file=self.output_file, mode='r') as zf:
            for info in zf.infolist():
                if info.filename.endswith(".shp"):
                    return datetime(*info.date_time)

        # dddd
        return None

    def to_geodtataframe(self) -> gpd.GeoDataFrame:
        """
        Lê o arquivo .zip baixado para o formato geodataframe

        :return: Geodataframe
        :rtype: gpd.GeoDataFrame
        """
        return gpd.read_file(filename=self.output_file)


if __name__ == '__main__':
    inc = INCRA(layer='Imóvel certificado SIGEF Privado', uf='RJ')
    print(inc._filename)
    print(inc._dropdown)
