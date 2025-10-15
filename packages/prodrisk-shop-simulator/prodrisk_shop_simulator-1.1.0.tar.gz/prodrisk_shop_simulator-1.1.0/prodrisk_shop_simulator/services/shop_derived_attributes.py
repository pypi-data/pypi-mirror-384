from pyshop import ShopSession

def get_max_time_delay(shop_session: ShopSession, river_name: str) -> int:
    """Get the maximum time delay for a river object, in hours.

    Note: river time delays are defined in hours, even though one can specify
    a 'time_delay_unit' as a global setting in SHOP.

    Args:
        shop_session: The SHOP session containing the model.
        river_name: The name of the river object.
    Returns:
        The maximum time delay in hours.
    """

    river_obj = shop_session.model["river"][river_name]
    
    time_delay_const = river_obj.time_delay_const.get()
    time_delay_curve = river_obj.time_delay_curve.get()

    if time_delay_curve is not None:
        max_time_delay = max(time_delay_curve.index)
    else:
        max_time_delay = time_delay_const #default 0, no time delay
    
    return max_time_delay