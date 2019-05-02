import logging
import smores.medkit as medkit

failures = []
def rxnorm_ingredient(rxcui, expect):
    _return_check=False
    _med_key_check=None
    _ing_key_check=None
    _overall=False
    _failures=[]
    ingredients = medkit.get_ingredients(rxcui, 'RXNORM')
    if ingredients is not None:
        if len(ingredients) > 0:
            if type(ingredients[0]) is dict:
                _return_check = True
            else:
                _failures.append('Return Check: Bad Return Type')
        if _return_check:
            default_keys = ['rxcui','tty','name','ingredients']
            med_1_keys = list(ingredients[0].keys())
            i=0
            while True:
                if i == len(med_1_keys)-1:
                    break
                elif default_keys[i] not in med_1_keys:
                    _failures.append('Med Check Failure: {0}'.format(default_keys[i]))
                    if _med_key_check:
                        _med_key_check = False
                    i += 1
                    continue
                else:
                    _med_key_check = True if _ing_key_check is None else False
                    i += 1
                    continue
            ing_1_keys = list(ingredients[0]['ingredients'][0].keys())
            ing_default_keys = ['rxcui', 'tty', 'name']
            j=0
            while True:
                if j == len(ing_1_keys)-1:
                    break
                elif ing_default_keys[j] not in ing_1_keys:
                    _failures.append('Med ING Check Failure: {0}'.format(ing_default_keys[j]))
                    if _ing_key_check:
                        _ing_key_check = False
                    j += 1
                    continue
                else:
                    _ing_key_check = True if _ing_key_check is None or _ing_key_check else _ing_key_check
                    j += 1
                    continue

    else:
        _failures.append('RxNav Check of {0} Failed All Checks'.format(rxcui))
    if _return_check and _med_key_check and _ing_key_check:
        _overall = True
    failures.append('{0}: {1} '.format(rxcui, _failures)) if len(_failures) > 0 else None
    if _overall == expect:
        print('RxNav Check of {0} Produced Expected Result of {1}'.format(rxcui, expect))
    else:
        print('RxNav Check of {0} Produced Unexpected Result of {1}'.format(rxcui, _overall))


if __name__ == "__main__":
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(funcName)-20s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    rxnormLog = logging.getLogger('rxnorm')
    smoresLog = logging.getLogger('smores')
    rxnormLog.addHandler(console)
    smoresLog.addHandler(console)

    rxnorm_ingredient('209387', True)
    rxnorm_ingredient('206410', False)
    rxnorm_ingredient('161', True)
    print(failures)