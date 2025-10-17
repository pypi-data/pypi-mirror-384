import jax
import jax.numpy as jnp
import jax.random as random


import sys
#sys.path.append('/Users/siddarth.chaturvedi/Desktop/source/abmax_git/abmax/')
from space.continuous.structs import *
from contexts.foraging.structs import *

def get_foragers_patches_interactions(foragers:Continous_circular_forager, patches:Continous_circular_patch):
    """
    steps:
    Calculate the energy_in and energy_out of the foragers and patches.active_state
        - Calculate the distance between the foragers and the patches. (each row is a forager, each column is a patch)
        - Calculate the energy that the foragers get from the patches. (each row is a forager, each column is a patch)
        - Foragers can get energy from multiple patches, thus sum the energy that the foragers get from the patches
        - A patch can feed multiple foragers, but in doing so it is depleted only once, by energy_offer amount. Thus take max of the energy matrix
    Args:
        - foragers: The foragers to calculate the energy_in and energy_out
        - patches: The patches to calculate the energy_in and energy_out
    Returns:
        - energy_in: The energy that the foragers get from the patches
        - energy_out: The energy that the patches give to

    """

    def forager_patches_dist(forager, patches):
        X_ps = patches.state.content['X'] # an array of shape (num_patches,)
        Y_ps = patches.state.content['Y']

        X_f = forager.state.content['X'] # a 1x1 array
        Y_f = forager.state.content['Y']
        
        return jnp.linalg.norm(jnp.stack((X_ps - X_f, Y_ps - Y_f), axis=1), axis=1)
    
    foragers_patches_dist = jax.vmap(forager_patches_dist, in_axes=(0, None))(foragers, patches)
    
    def forager_patches_energy(forager_patches_dist):
        def forager_patch_energy(dist, energy_offer, rad):
            return jax.lax.cond(dist[0] < rad[0], lambda _: energy_offer[0], lambda _: 0.0, None)
        return jax.vmap(forager_patch_energy, in_axes=(0, 0, 0))(forager_patches_dist, patches.state.content['energy_offer'], patches.state.content['radius'])
    
    foragers_patches_energy = jax.vmap(forager_patches_energy)(foragers_patches_dist)
    
    energy_in = jnp.sum(foragers_patches_energy, axis=1)# sum and not max because if there is overlapping resources, the forager can get energy from both
    energy_out = jnp.sum(foragers_patches_energy, axis=0)# does not matter as this is used as a boolean thus sum is the same as max
    
    return energy_in, energy_out

jit_get_foragers_patches_interactions = jax.jit(get_foragers_patches_interactions)


def get_sensor_data(foragers:Continous_circular_forager, patches:Continous_circular_patch, walls:Line):
    """
    Get the sensor data for the foragers. For each forager, for each ray -> [energy, type, distance]
    energy: The energy of the entity that the ray intercepts, nothing->0.0 wall -> 0.0, forager -> energy, patch -> energy
    type: The type of the entity that the ray intercepts, nothing->0, wall -> 1, forager -> 2, patch -> 3
    distance: The distance of the entity that the ray intercepts, nothing->ray_length, wall -> distance, forager -> distance, patch -> distance
    Args:
        foragers: The foragers to get the sensor data
        patches: The patches to get the sensor data
        walls: The walls in the space
    Returns:
        The sensor data for the foragers
    """
    
    agent_xs = jnp.concatenate([jnp.reshape(foragers.state.content['X'], (-1)), jnp.reshape(patches.state.content['X'], -1)])
    agent_ys = jnp.concatenate([jnp.reshape(foragers.state.content['Y'], (-1)), jnp.reshape(patches.state.content['Y'], -1)])
    agent_rads = jnp.concatenate([jnp.reshape(foragers.state.content['radius'], (-1)), jnp.reshape(patches.state.content['radius'], -1)])
    agent_types = jnp.concatenate([jnp.reshape(foragers.agent_type, (-1)), jnp.reshape(patches.agent_type, -1)])
    agent_active_states = jnp.concatenate([jnp.reshape(foragers.active_state, (-1)), jnp.reshape(patches.active_state, -1)])

    entity_types = jnp.concatenate([agent_types, jnp.ones_like(walls.p1.x)]) # 0->nothing, 1->wall, 2->forager, 3->patch
    entity_energies = jnp.concatenate([jnp.reshape(foragers.state.content['energy'], (-1)), jnp.reshape(patches.state.content['energy'], -1), jnp.zeros_like(walls.p1.x)])
    entity_energies = jnp.maximum(entity_energies, 0.0) # agents cant see negative energy
    #entity_ids = jnp.concatenate([jnp.reshape(foragers.id, (-1)), jnp.reshape(patches.id, -1), jnp.zeros_like(walls.p1.x)])
    env_states = jnp.vstack([entity_types, entity_energies]) # shape = (2, num_entities)

    #to speed up the computation, we can concatenate the wall information to the agent information
    data_ax_wp1x = jnp.concatenate([agent_xs, walls.p1.x]) # contains x coordinates of the agents and the beginning of the walls
    data_ay_wp1y = jnp.concatenate([agent_ys, walls.p1.y]) # contains y coordinates of the agents and the beginning of the walls
    data_ar_wp2x = jnp.concatenate([agent_rads, walls.p2.x]) # contains radii of the agents and the end of the walls
    data_aa_wp2y = jnp.concatenate([agent_active_states, walls.p2.y]) # contains active states of the agents and the end of the walls

    data_tuple = (data_ax_wp1x, data_ay_wp1y, data_ar_wp2x, data_aa_wp2y)
    
    def get_forager_sensor(forager):

        ray_span = RAY_SPAN # define the global variable
        ray_max_length = RAY_MAX_LENGTH # define the global variable
        forager_pos = (forager.state.content['X'][0], forager.state.content['Y'][0], forager.state.content['ang'][0]) #shape = (3,1)
        rays = generate_rays(forager_pos, ray_span, ray_max_length)

        def get_ray_sensor(ray):
        
            def get_ray_entity_sensor(data_tuple_row, entity_type):
                
                def ray_agent_collision():
                    circle = Circle(center = Point(data_tuple_row[0], data_tuple_row[1]), radius = data_tuple_row[2])
                    return jit_get_ray_circle_collision(ray, circle)
                
                def ray_wall_collision():
                    wall = Line(p1 = Point(data_tuple_row[0], data_tuple_row[1]), p2 = Point(data_tuple_row[2], data_tuple_row[3]))
                    return jit_get_ray_wall_collision(ray, wall)
                
                ray_collision = jax.lax.cond(entity_type == 1, lambda _: ray_wall_collision(), lambda _: ray_agent_collision(), None)
                return ray_collision
            
            ray_intercept_dist = jax.vmap(get_ray_entity_sensor)(data_tuple, entity_types)
            
            min_intercept_dist = jnp.min(ray_intercept_dist)
            min_intercept_index = jnp.argmin(ray_intercept_dist)
            min_intercept_index = jax.lax.cond(min_intercept_dist < ray_max_length, lambda _: min_intercept_index, lambda _: -1, None) # if the ray does not intercept with anything, return -1

            def get_sensor_data(env_states_row, min_intercept_index):
                return jax.lax.cond(min_intercept_index < 0, lambda _:0.0, lambda _: env_states_row[min_intercept_index], None) # 0.0 is energy value and type as wall is type 1
            
            sensor_data = jax.vmap(get_sensor_data, in_axes=(0, None))(env_states, min_intercept_index)# this vmap iterates over env_states = [entity_types, entity_energies], axis = 0
            
            ray_sensor= jnp.concatenate((sensor_data, jnp.array([min_intercept_dist])))

            return ray_sensor

        forager_sensor = jax.vmap(get_ray_sensor)(rays)
        return jnp.reshape(forager_sensor, (-1))
    
    foragers_sensor = jax.vmap(get_forager_sensor)(foragers)
    

    return foragers_sensor

        
jit_get_sensor_data = jax.jit(get_sensor_data)

