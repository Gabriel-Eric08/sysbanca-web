def num_animal_grupo(numero):
    """
    Calcula o grupo e animal a partir de um número de prêmio.
    Retorna uma lista com o número do prêmio (string), o grupo (string com 2 dígitos) e o animal.

    Args:
        numero (str): O número do prêmio como uma string.

    Returns:
        list: Uma lista contendo o número do prêmio (string), o grupo (string com 2 dígitos) e o animal (string).
    """
    animais = [
        'AVESTRUZ', 'ÁGUIA', 'BURRO', 'BORBOLETA', 'CACHORRO', 'CABRA',
        'CARNEIRO', 'CAMELO', 'COBRA', 'COELHO', 'CAVALO', 'ELEFANTE',
        'GALO', 'GATO', 'JACARÉ', 'LEÃO', 'MACACO', 'PORCO', 'PAVÃO',
        'PERU', 'TOURO', 'TIGRE', 'URSO', 'VEADO', 'VACA'
    ]

    try:
        # Guarda o valor original como string antes de converter
        numero_str = str(numero)
        numero_int = int(numero_str)

        if numero_int < 0 or numero_int > 9999:
            raise ValueError("O número deve ter até 4 dígitos.")

        # Pega os dois últimos dígitos do valor inteiro para o cálculo
        ultimos_dois = numero_int % 100
        if ultimos_dois == 0:
            ultimos_dois = 100

        grupo_int = (ultimos_dois - 1) // 4 + 1
        
        # Formata o número do grupo para ter sempre 2 dígitos
        grupo_str = f"{grupo_int:02d}"
        
        animal = animais[grupo_int - 1]

        # Retorna o número original como string
        res = [numero_str, grupo_str, animal]
        return res
    except Exception as e:
        return str(e)