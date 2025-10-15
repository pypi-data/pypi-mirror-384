"""
arthub_api.asset_matrix
~~~~~~~~~~~~~~

This module provides the operation interface of the ArtHub asset matrix module
To visit the page of the asset matrix module:
"https://arthub.qq.com/apg/assetMatrix/progress/progress"
"""


class AssetMatrix(object):
    def __init__(self, open_api):
        r"""Used to perform ArtHub asset matrix operations, such as production task management.

        :param open_api: class: arthub_api.API.
        """
        self.open_api = open_api
