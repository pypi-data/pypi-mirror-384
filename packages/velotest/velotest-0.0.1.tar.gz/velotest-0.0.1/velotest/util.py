import numpy as np
import torch
import matplotlib.pyplot as plt


def plot_angle_statistic(cell, Z_expr, Z_velocity, uncorrected_p_values, test_statistics_random, test_statistics_velocity, neighborhoods, Z_velo_position_random, name="scvelo", ax=None, scatter_size=None):
    if ax is None:
        fig, ax = plt.subplots()

    if isinstance(Z_velo_position_random, torch.Tensor):
        random_velocity_positions = Z_velo_position_random.detach().clone()
    else:
        random_velocity_positions = torch.tensor(Z_velo_position_random)

    non_empty_neighborhoods_indices = np.where(uncorrected_p_values != 2)[0]
    converted_cell = torch.where(torch.tensor(non_empty_neighborhoods_indices) == cell)[0]

    # Assumes neighborhoods to be without the velocity neighborhood, otherwise use "neighborhoods_one_cell[1:]"
    non_empty_random_neighborhoods = [
        np.array([len(neighborhood) > 0 for neighborhood in neighborhoods_one_cell]) for neighborhoods_one_cell in
        neighborhoods]
    non_empty_random_neighborhoods_indices = [np.where(neighborhoods_one_cell)[0] for neighborhoods_one_cell in
                                                   non_empty_random_neighborhoods]

    x_all = (random_velocity_positions[cell] - Z_expr[cell])
    angles = torch.atan2(x_all[:, 1], x_all[:, 0])
    indices_ordered_angles = torch.argsort(angles)
    unit_circle_positions = angles[non_empty_random_neighborhoods_indices[cell]]
    test_statistics = test_statistics_random[converted_cell]
    ax.scatter(unit_circle_positions, test_statistics, label="random velocities", s=scatter_size, c="#02ADFF")
    ax.vlines(torch.atan2(torch.tensor(Z_velocity[cell, 1]), torch.tensor(Z_velocity[cell, 0])), ax.get_ylim()[0], ax.get_ylim()[1], color='black',
               linestyle='dashed', linewidth=1, label=f"{name}'s velocity: {test_statistics_velocity[converted_cell]:.2f}")
    ax.set_ylabel("Test statistic")
    ax.set_xlabel("Position on unit circle [rad]")
    ax.set_title(f"Cell {cell} - test statistic for random velocities")
    ax.legend()
    return unit_circle_positions, test_statistics


def plot_angle_statistic_violin(cell, uncorrected_p_values, neighborhoods, cos_neighborhoods, random_velocity_positions, Z_expr):
    fig = plt.figure(figsize=(10, 5))
    non_empty_neighborhoods_indices = np.where(uncorrected_p_values != 2)[0]
    converted_cell = torch.where(torch.tensor(non_empty_neighborhoods_indices) == cell)[0]
    # number_neighborhoods_to_show = 30

    non_empty_random_neighborhoods = [
        np.array([len(neighborhood) > 0 for neighborhood in neighborhoods_one_cell[1:]]) for neighborhoods_one_cell in
        neighborhoods]
    non_empty_random_neighborhoods_indices = [np.where(neighborhoods_one_cell)[0] for neighborhoods_one_cell in
                                              non_empty_random_neighborhoods]

    x_all = (random_velocity_positions[cell] - Z_expr[cell])
    angles = torch.atan2(x_all[:, 0], x_all[:, 1])
    #angles = angles[non_empty_random_neighborhoods_indices[converted_cell]]
    #indices_ordered_angles = torch.argsort(angles)
    # chose_every_n_angle = int(len(angles)/number_neighborhoods_to_show)
    #chosen_angles_indices = [index for i, index in enumerate(indices_ordered_angles)]  # if i % chose_every_n_angle == 0
    #chosen_angles_indices = np.array(chosen_angles_indices)

    # plt.violinplot([[cos_neighborhoods[converted_cell][ind] for ind in non_empty_random_neighborhoods_indices[converted_cell]][index] for index in chosen_angles_indices], positions=angles[non_empty_random_neighborhoods_indices[converted_cell]][chosen_angles_indices].numpy(), showmeans=True)
    # plt.scatter(angles[non_empty_random_neighborhoods_indices[converted_cell]][chosen_angles_indices].numpy(), [[torch.mean(cos_neighborhoods[converted_cell][ind]) for ind in non_empty_random_neighborhoods_indices[converted_cell]][index] for index in chosen_angles_indices], )
    plt.scatter(angles[non_empty_random_neighborhoods_indices[converted_cell]].numpy(),
                [torch.mean(cos_neighborhoods[converted_cell][ind]) for ind in
                 non_empty_random_neighborhoods_indices[converted_cell]])