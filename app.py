from flask import Flask, render_template, request, redirect, url_for, session
import requests
import random

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

def get_pokemon_by_id(pokemon_id):
    """Fetch a single pokemon by ID"""
    base_url = "https://pokeapi.co/api/v2/pokemon"
    
    try:
        response = requests.get(f"{base_url}/{pokemon_id}")
        response.raise_for_status()
        pokemon_data = response.json()
        
        stats = {stat['stat']['name']: stat['base_stat'] for stat in pokemon_data['stats']}
        total_stats = sum(stats.values())
        
        return {
            'id': pokemon_data['id'],
            'name': pokemon_data['name'],
            'height': pokemon_data['height'],
            'weight': pokemon_data['weight'],
            'base_experience': pokemon_data.get('base_experience'),
            'types': [type_info['type']['name'] for type_info in pokemon_data['types']],
            'stats': stats,
            'total_stats': total_stats,
            'sprites': {
                'front_default': pokemon_data['sprites']['front_default'],
                'front_shiny': pokemon_data['sprites'].get('front_shiny')
            }
        }
    except requests.exceptions.RequestException as e:
        return None

def get_random_pokemons(count=2, max_id=1000):
    """Fetch random pokemons"""
    pokemons = []
    
    # Generate random IDs
    random_ids = random.sample(range(1, max_id + 1), count)
    
    for pokemon_id in random_ids:
        pokemon = get_pokemon_by_id(pokemon_id)
        if pokemon:
            pokemons.append(pokemon)
        else:
            # If failed, try another random ID
            while len(pokemons) < count:
                new_id = random.randint(1, max_id)
                if new_id not in random_ids:
                    pokemon = get_pokemon_by_id(new_id)
                    if pokemon:
                        pokemons.append(pokemon)
                        break
    
    return pokemons if len(pokemons) == count else None

def calculate_battle_power(pokemon):
    """Calculate battle power based on stats"""
    stats = pokemon['stats']
    # Weighted calculation: HP, Attack, Defense, Special Attack, Special Defense, Speed
    battle_power = (
        stats.get('hp', 0) * 1.0 +
        stats.get('attack', 0) * 1.2 +
        stats.get('defense', 0) * 1.0 +
        stats.get('special-attack', 0) * 1.2 +
        stats.get('special-defense', 0) * 1.0 +
        stats.get('speed', 0) * 0.8
    )
    return battle_power

def battle_pokemons(pokemon1, pokemon2):
    """Battle two pokemons and return the winner"""
    power1 = calculate_battle_power(pokemon1)
    power2 = calculate_battle_power(pokemon2)
    
    if power1 > power2:
        return pokemon1, pokemon2, power1, power2
    elif power2 > power1:
        return pokemon2, pokemon1, power2, power1
    else:
        return None, None, power1, power2  # Tie

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/start_battle', methods=['POST'])
def start_battle():
    """Start a new battle by fetching 2 random pokemons"""
    pokemons = get_random_pokemons(2)
    
    if not pokemons or len(pokemons) != 2:
        return render_template('index.html', error="Failed to fetch pokemons. Please try again.")
    
    # Store pokemons in session
    session['pokemon1'] = pokemons[0]
    session['pokemon2'] = pokemons[1]
    
    return redirect(url_for('select_pokemon'))

@app.route('/select')
def select_pokemon():
    """Display pokemons for selection"""
    pokemon1 = session.get('pokemon1')
    pokemon2 = session.get('pokemon2')
    
    if not pokemon1 or not pokemon2:
        return redirect(url_for('index'))
    
    return render_template('select.html', pokemon1=pokemon1, pokemon2=pokemon2)

@app.route('/battle', methods=['POST'])
def battle():
    """Process the battle"""
    choice = request.form.get('choice')
    pokemon1 = session.get('pokemon1')
    pokemon2 = session.get('pokemon2')
    
    if not pokemon1 or not pokemon2:
        return redirect(url_for('index'))
    
    # Determine player and opponent pokemon
    if choice == '1':
        player_pokemon = pokemon1
        opponent_pokemon = pokemon2
    elif choice == '2':
        player_pokemon = pokemon2
        opponent_pokemon = pokemon1
    else:
        return redirect(url_for('select_pokemon'))
    
    # Battle
    winner, loser, winner_power, loser_power = battle_pokemons(player_pokemon, opponent_pokemon)
    
    # Determine if player won
    player_won = winner == player_pokemon
    is_tie = winner is None
    
    return render_template('result.html', 
                         player_pokemon=player_pokemon,
                         opponent_pokemon=opponent_pokemon,
                         winner=winner,
                         loser=loser,
                         player_won=player_won,
                         is_tie=is_tie)

if __name__ == '__main__':
    app.run(debug=True)

