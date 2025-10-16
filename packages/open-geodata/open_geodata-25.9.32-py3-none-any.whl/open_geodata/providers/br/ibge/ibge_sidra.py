"""
sssss

"""

import sidrapy
import pandas as pd


def get_estimated_population(id_municipio):
    """
    Retorna a população estimada
    :param id_municipio:
    :return:
    """
    # Get Table
    df = sidrapy.get_table(
        table_code='6579',
        territorial_level='6',
        ibge_territorial_code=id_municipio,
        period='all',
        header='n',
    )

    # Dict
    dict_col = {
        'D1C': 'id_municipio',
        'D1N': 'municipio_nome',
        'V': 'n_habitantes',
        'D2N': 'ano',
    }

    # Rename Columns
    df = df.rename(dict_col, axis=1, inplace=False)

    # Select Columns
    df = df[[v for k, v in dict_col.items()]]

    # Adjust Columns
    df = df.sort_values(by=['ano'], inplace=False)
    df['id_municipio'] = pd.to_numeric(df['id_municipio'], errors='coerce')
    df['n_habitantes'] = pd.to_numeric(df['n_habitantes'], errors='coerce')
    df['ano'] = pd.to_numeric(df['ano'], errors='coerce')

    # Results
    return df


if __name__ == '__main__':
    cod_ibge = '3526902'  # Limeira
    pop = get_estimated_population(cod_ibge)
    print(pop)
