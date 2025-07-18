def num_animal_grupo(numero):
    animais = [
        'AVESTRUZ', 'ÁGUIA', 'BURRO', 'BORBOLETA', 'CACHORRO', 'CABRA',
        'CARNEIRO', 'CAMELO', 'COBRA', 'COELHO', 'CAVALO', 'ELEFANTE',
        'GALO', 'GATO', 'JACARÉ', 'LEÃO', 'MACACO', 'PORCO', 'PAVÃO',
        'PERU', 'TOURO', 'TIGRE', 'URSO', 'VEADO', 'VACA'
    ]

    try:
        numero = int(numero)
        if numero < 0 or numero > 9999:
            raise ValueError("O número deve ter até 4 dígitos.")
        
        # Pega os dois últimos dígitos
        ultimos_dois = numero % 100
        if ultimos_dois == 0:
            ultimos_dois = 100
        
        grupo = (ultimos_dois - 1) // 4 + 1
        animal = animais[grupo - 1]

        res = [numero, grupo, animal]
        return res
    except Exception as e:
        return str(e)