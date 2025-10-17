__all__ = ["fold_scan", "value_scan"]

from ._helper.helper import UnittedLinSpace, UnittedLogSpace
from ._helper.parser import parse_unitted_number
from ._scan_ast import AddScan, FoldScan, NoScan, Scan, ValueScan, ZipScan


def value_scan(**kwargs: list[float | str] | UnittedLinSpace | UnittedLogSpace) -> Scan:
    """Generate a list of scan values from the keyword arguments.

    Each parameter to scan should be passed as an argument with
    a list that contains the values to scan and the parameter's unit.

    Parameters
    ----------
    **kwargs : list[float | str] | UnittedLinSpace | UnittedLogSpace
        Keywords are the parameters to scan, and values are a list of parameter values or
        UnittedLinSpace or UnittedLogSpace objects.
        If the parameter is a unitless parameter, the value should be a float.
        If the parameter has a unit, the value should be a string with the unit divided by :.

    Returns
    -------
    Scan

    Examples
    --------
    >>> value_scan(koff=[1,2,3])
    Specifies three simulations, one for each value of parameter `koff`.

    >>> value_scan(koff=["1:1/s","2:1/s","3:1/s"])
    Specifies three simulations, one for each value of parameter `koff`.

    >>> value_scan(Kd=[1,2,3], kon=[1e-3,2e-3,3e-3])
    Specifies three simulations, one for each pair of values of parameters `Kd` and `kon`.
    """

    zip_scans = []
    for key, values in kwargs.items():
        if isinstance(values, UnittedLinSpace) or isinstance(values, UnittedLogSpace):
            values = values.to_list()
        add_scans = []
        for value in values:
            if isinstance(value, str):
                v, u = parse_unitted_number(value)
                vs = ValueScan(name=key, value=v, unit=u)
            else:
                vs = ValueScan(name=key, value=float(value))
            add_scans.append(vs)
        zip_scans.append(generate_add_scans(add_scans))
    all_scans = generate_zip_scans(zip_scans)
    return all_scans


def fold_scan(**kwargs: list[float]) -> Scan:
    """Generate a list of scan fold changes from the keyword arguments.

    Each parameter to scan should be passed as an argument with
    a list that contains the fold changes to scan.

    Parameters
    ----------
    **kwargs : list[float]
        Keywords are the parameters to scan, and values are the parameter fold changes.
        Units will be determined from the model or parameter table.

    Returns
    -------
    Scan

    Examples
    --------
    >>> fold_scan(koff=[1,2,3])
    Specifies three simulations, one for each fold change of parameter `koff`.

    >>> fold_scan(Kd=[1,2,3], kon=[1e-3,2e-3,3e-3])
    Specifies three simulations, one for each pair of fold changes of parameters `Kd` and `kon`.
    """

    zip_scans = []
    for key, values in kwargs.items():
        add_scans = []
        for value in values:
            fs = FoldScan(name=key, fold=float(value))
            add_scans.append(fs)
        zip_scans.append(generate_add_scans(add_scans))
    all_scans = generate_zip_scans(zip_scans)
    return all_scans


def generate_add_scans(scans: list[Scan]) -> Scan:
    if len(scans) == 0:
        return NoScan()

    add_scan = scans[0]
    for i in range(1, len(scans), 1):
        add_scan = AddScan(add_scan, scans[i])
    return add_scan


def generate_zip_scans(scans: list[Scan]) -> Scan:
    if len(scans) == 0:
        return NoScan()

    zip_scan = scans[0]
    for i in range(1, len(scans), 1):
        zip_scan = ZipScan(zip_scan, scans[i])
    return zip_scan
