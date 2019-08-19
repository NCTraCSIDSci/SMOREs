# # testing UMLS crosswalks and SNOMED
from smores.api import UMLS
from smores.utility import util

umls = UMLS()
print('###################TESTING SNOWMED CROSSWALKS############################################')
print('\nTesting lookup of SNOMED codes by ID')
print(umls.get_snomed_by_id('387207008'))
print('\nTesting crosswalk from SNOMED (387207008, Ibuprofen) to RXNORM')
print(umls.crosswalk_UMLS('387207008', 'snomedct_us', 'rxnorm'))
print('\nTesting crosswalk from SNOMED (370152009, Acetaminophen) to NDC')
print(umls.crosswalk_UMLS('370152009', 'SNOMEDCT_US', 'NDC'))
#input('\nPress <ENTER> to continue')

print('\n####################TESTING RXNORM CROSSWALKS##########################################')
print('\nTesting crosswalk from RXNORM to SNOMED')
print(umls.crosswalk_UMLS('198436', 'RXNORM', 'SNOMEDCT_US'))
print(umls.crosswalk_UMLS('1738139', 'RXNORM', 'SNOMEDCT_US'))
print(umls.crosswalk_UMLS('1044427', 'RXNORM', 'SNOMEDCT_US'))
print('\nTesting crosswalk from RXNORM to NDC')
print(umls.crosswalk_UMLS('198436', 'RXNORM', 'NDC'))
#input('\nPress <ENTER> to continue')

print('\n####################### TESTING NDC CROSSWALKS##########################################')
print('\nTesting crosswalk from NDC to RXNORM')
print(umls.crosswalk_UMLS('0004-0038-22', 'NDC', 'RXNORM'))
print('\nTesting crosswalk from NDC to SNOMED')
print(umls.crosswalk_UMLS('0004-0038-22', 'NDC', 'SNOMEDCT_US'))
#input('\nPress <ENTER> to continue')

print('\n####################### TESTING UMLS CROSSWALKS##########################################')
print('\nTesting crosswalk from UMLS to SNOMEDCT_US')
print(umls.crosswalk_UMLS('C0691084', 'UMLS', 'SNOMEDCT_US'))
print('\nTesting crosswalk from UMLS to RXNORM')
print(umls.crosswalk_UMLS('C0691084', 'UMLS', 'RXNORM'))
#input('\nPress <ENTER> to continue')

print('\n####################### TESTING OTHER CROSSWALKS##########################################')
print('\nTesting crosswalk from CPT to HCPT')
print(umls.crosswalk_UMLS('67005', 'CPT', 'HCPT'))
print('\nTesting crosswalk from HCPT to CPT')
print(umls.crosswalk_UMLS('67010', 'HCPT', 'CPT'))
print('\nTesting crosswalk from CPT to SNOMED')
print(umls.crosswalk_UMLS('67005', 'CPT', 'SNOMEDCT_US'))
print('\nTesting the output of invalid inputs')
print(umls.crosswalk_UMLS('67005', 'invalid_codeset', 'invalid_codeset'))
#input('\nPress <ENTER> to continue')


print('\n####################### TESTING VALIDATION FUNCTION##########################################')
print(umls.validate('387207008', 'SNOMEDCT_US'))
print(umls.validate('1', 'SNOMEDCT_US'))
#input('\nPress <ENTER> to continue')


print('\n####################### TESTING STATUS FUNCTION##########################################')
print(umls.get_code_status('387207008', 'SNOMEDCT_US'))
print(umls.get_code_status('362955004', 'SNOMEDCT_US'))
print(umls.get_code_status('198436', 'RXNORM'))
print(umls.get_code_status('67005', 'CPT'))
print(umls.get_code_status('1', 'SNOMEDCT_US'))
print('\nFinished Test Script')

