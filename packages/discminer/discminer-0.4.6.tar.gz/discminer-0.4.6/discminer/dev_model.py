def get_model_parameters():
    params = {
        'velocity': {
            'Mstar': 1.0,
            'vel_sign': 1,
            'vsys': 0
        },
        'orientation': {
            'incl': 0.7,
            'PA': 0.0,
            'xc': 0.0,
            'yc': 0.0
        },
        'intensity': {
            'I0': 0.5,
            'p': -1.5, 
            'q': 2.0,
            'Rout': 500
        },
        'linewidth': {
            'L0': 0.3, 
            'p': -0.5, 
            'q': -0.3
        }, 
        'lineslope': {
            'Ls': 2.0, 
            'p': 0.3, 
            'q': 0.0
        },
        'height_upper': {
            'z0': 40.0,
            'p': 1.0,
            'Rb': 500,
            'q': 2.0
        },
        'height_lower': {
            'z0': 20.0,
            'p': 1.0,
            'Rb': 500,
            'q': 2.0
        }
    }

def get_model_functions(disc=None, depth='thick', mol='12co'):

    model_funcs = copy.copy(_func_defaults)
    
    if disc in [None, 'mwc480']:
        z_upper_func = z_upper_exp_tapered
        z_lower_func = z_lower_exp_tapered
        intensity_func = intensity_powerlaw_rout
        linewidth_func = linewidth_powerlaw
        lineslope_func = lineslope_powerlaw
        
    if depth=='thick':
        model_funcs.update({'line_profile': line_profile_bell})
        line_uplow = line_uplow_mask

    elif depth=='thin':
        line_profile = line_profile_gaussian
        line_uplow = line_uplow_sum
    
#On INIT MODEL
#Could be the other way around, initialise datacube=Cube(...), inherit Model class which receives datacube and other parameters. Then all required info for metadata is in self object. If I decide to stick to the current version perhaps I should rename this as ReferenceCube or ModelCube instead?
