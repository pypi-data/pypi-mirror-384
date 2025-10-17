
from abmax.structs import *
from abmax.functions import *
import jax
import jax.random as random
import jax.numpy as jnp
from flax import struct



@struct.dataclass
class Continous_circular_forager(Agent):

    @staticmethod
    def create_agent(type, params, id, active_state, key):
        """
        The forager agent is created with the following design choices:
        - The forager is created with a random position in the space
        - The forager is created with a random velocity in the space
        - THe energy is initialized to energy_begin
        - The radius is initialized to radius and remains constant
        - The forager is created with a random policy

        state:
            - X: The x coordinate of the forager
            - Y: The y coordinate of the forager
            - X_dot: The x velocity of the forager
            - Y_dot: The y velocity of the forager
            - ang: The angle of the forager
            - energy: The energy of the forager
            - radius: The radius of the forager
        params:
            - space: The space in which the forager is created
            - energy_max: The maximum energy the forager can have
            - energy_min: The minimum energy the forager can have
            - energy_begin: The initial energy of the forager
            - radius: The radius of the forager
        Args:
            type: The type of the agent
            params: The parameters of the agent
            id: The id of the agent
            active_state: The active state of the agent
            key: The key used for random number generation
        Returns:
            A new forager agent
        """
        policy = params.content['policy']
        agent_params_content = {'space': params.content['space'], 'energy_max': params.content['energy_max'], 'energy_min': params.content['energy_min'], 'energy_begin': params.content['energy_begin']}
        agent_params = Params(content = agent_params_content)

        key, subkey = random.split(key)
        def create_active_state():
            _key, *create_keys = random.split(subkey, 5)
            X_len = params.content['space'].x_max - params.content['space'].x_min
            Y_len = params.content['space'].y_max - params.content['space'].y_min

            X = random.uniform(create_keys[0], (1,), minval=params.content['space'].x_min + 0.01*X_len, maxval=params.content['space'].x_max - 0.01*X_len)
            Y = random.uniform(create_keys[1], (1,), minval=params.content['space'].y_min + 0.01*Y_len, maxval=params.content['space'].y_max - 0.01*Y_len)
            vel_begin = params.content['vel_begin']
            X_dot = random.uniform(create_keys[2], (1,), minval=-vel_begin, maxval=vel_begin)
            Y_dot = random.uniform(create_keys[3], (1,), minval=-vel_begin, maxval=vel_begin)
            ang = jnp.arctan2(Y_dot, X_dot)

            energy = jnp.array([params.content['energy_begin']])
            radius = jnp.array([params.content['radius']])

            state_content = {'X': X, 'Y': Y, 'X_dot': X_dot, 'Y_dot': Y_dot, 'ang':ang, 'energy': energy, 'radius': radius}
            return State(content = state_content)
        
        def create_inactive_state():
            state_content = {'X': jnp.array([0.0]), 'Y': jnp.array([0.0]), 'X_dot': jnp.array([0.0]), 'Y_dot': jnp.array([0.0]), 'ang': jnp.array([0.0]), 
                             'energy': jnp.array([0.0]), 'radius': jnp.array([0.0])}
            return State(content = state_content)
        
        forager_state = jax.lax.cond(active_state, lambda _: create_active_state(), lambda _: create_inactive_state(), None)
        return Continous_circular_forager(id = id, active_state = active_state, age = 0.0, agent_type = type, params = agent_params, state = forager_state, policy = policy, key = key)
    



@struct.dataclass
class Continous_circular_patch(Agent):
    
    @staticmethod
    def create_agent(type, params, id, active_state, key):
        """
        Create a new patch agent with the given type, parameters, id, active state and key.
        Patch agent:
        state:
            - X: The x coordinate of the patch
            - Y: The y coordinate of the patch
            - energy: The energy of the patch
            - radius: The radius of the patch
            - energy_offer: The energy offer of the patch
        params:
            - eat_constant: The constant that determines how much energy is offered to the eater, energy_offer = eat_constant*energy
            - growth_rate: The rate at which the patch grows
            - energy_max: The maximum energy the patch can have
            - energy_min: The minimum energy the patch can have
            - space: The space in which the patch is created
        Design choices:
            - The patch is created with a random position in the space
            - All patches begin with the same energy and radius
            - radius remains constant
            - constant growth rate
        Args:
            - type: The type of the agent
            - params: The parameters of the agent
            - id: The id of the agent
            - active_state: The active state of the agent
            - key: The key used for random number generation
        Returns:
            A new patch agent
        """
        key, subkey = random.split(key)
        def create_active_state():
            _key, *create_keys = random.split(subkey,3)
        
            patch_radius = params.content['radius']
            space = params.content['space']
            space_x_len_margin = 0.01*(space.x_max - space.x_min) + patch_radius
            space_y_len_margin = 0.01*(space.y_max - space.y_min) + patch_radius

            X = random.uniform(create_keys[0], (1,), minval=space.x_min + space_x_len_margin, maxval=space.x_max - space_x_len_margin)
            Y = random.uniform(create_keys[1], (1,), minval=space.y_min + space_y_len_margin, maxval=space.y_max - space_y_len_margin)
            # We don't wall the patch to be to close to the edge of the space
            # right now uniform random initialization

            energy = jnp.array([params.content['energy_begin']])
            # all the patches start with the same energy

            radius = jnp.array([params.content['radius']])
            # all the patches have the same radius, it remains constant

            energy_offer = params.content['eat_constant']*energy
            # A certain amount of energy is up for grabs

            state_content = {'X': X, 'Y': Y, 'energy': energy, 'radius': radius, 'energy_offer': energy_offer}
            return State(content = state_content)
        
        # there are no inactive patches in the environment
        def create_inactive_state():
            state_content = {'X': jnp.array([0.0]), 'Y': jnp.array([0.0]), 'energy': jnp.array([0.0]), 'radius': jnp.array([0.0]), 'energy_offer': jnp.array([0.0])}
            return State(content = state_content)
        
        patch_state = jax.lax.cond(active_state, lambda _: create_active_state(), lambda _: create_inactive_state(), None)
        space = params.content['space']
        patch_params_content = {'eat_constant': params.content['eat_constant'], 'growth_rate': params.content['growth_rate'],
                                'energy_max': params.content['energy_max'], 'energy_min': params.content['energy_min'], 'x_max':space.x_max,
                                'y_max':space.y_max}
        # these params are apparently constants and not 1x1 arrays
        patch_params = Params(content = patch_params_content)

        return Continous_circular_patch(id = id, active_state = active_state, age = 0.0, agent_type = type, params = patch_params, state = patch_state, policy = None, key = key)
    