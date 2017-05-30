import pycity.functions.changeResolution as chres


def run_change_res_mean_timestep():

    timestep_old = 3600
    timestep_new = 900
    input_array = [10, 20]

    output_array = chres.changeResolution(values=input_array,
                                            oldResolution=timestep_old,
                                            newResolution=timestep_new,
                                            method="mean")

    print(output_array)

    timestep_old = 900
    timestep_new = 3600

    output_array2 = chres.changeResolution(values=output_array,
                                            oldResolution=timestep_old,
                                            newResolution=timestep_new,
                                            method="mean")

    print(output_array2)

def run_change_res_sum_timestep():

    timestep_old = 3600
    timestep_new = 900
    input_array = [60, 20]

    output_array = chres.changeResolution(values=input_array,
                                            oldResolution=timestep_old,
                                            newResolution=timestep_new,
                                            method="sum")

    print(output_array)

    timestep_old = 900
    timestep_new = 3600

    output_array2 = chres.changeResolution(values=output_array,
                                            oldResolution=timestep_old,
                                            newResolution=timestep_new,
                                            method="sum")

    print(output_array2)


if __name__ == '__main__':
    run_change_res_mean_timestep()
    run_change_res_sum_timestep()