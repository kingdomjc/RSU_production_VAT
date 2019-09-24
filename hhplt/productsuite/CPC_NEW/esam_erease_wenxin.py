import binascii
import os

from SM4.sm4_gm import *
from SM4.print_log import *
from hhplt.parameters import PARAM

HFCARD_COMMAND = None
activeEsam = None



key_all_zero = "00000000000000000000000000000000"


# encrpty and decrpty value
ENCRYPT = 0
DECRYPT = 1
#log_init() #enable print_data function

# delivery or not
DE_DELIVERY    = 0
EN_DELIVERY    = 1
EN_DELIVERY_L1 = 1
EN_DELIVERY_L2 = 2


# defaultkey = "B629FC012B2F234E97A00972E530C752"
# defaultkey_Hex = [0xB6, 0x29, 0xFC, 0x01, 0x2B, 0x2F, 0x23, 0x4E,
                # 0x97, 0xA0, 0x09, 0x72, 0xE5, 0x30, 0xC7, 0x52]

init_defaultkey = "B629FC012B2F234E97A00972E530C752"


UK1_rootkey = "B629FC012B2F234E97A00972E530C752"
UK2_rootkey = "B8BBC7BFC3F1D6F7CEC4C3F7BACDD0B3"
IK1_rootkey = "B2BBCDFCB3F5D0C4C0CEBCC7CAB9C3FC"

# default master key
defaultkey = ''
defaultkey_Hex = []

cpc_sn = '' # CPC SN variable
cpc_id = '' # CPC ID variable

area_code = '' # area code variable

# new system information to update
new_sysinfo = ''

# key for update system information
key_for_sysinfor = ''



# function: string convert to hex
def str_to_hex(str_to_switch):	
	init_datahex = binascii.unhexlify(str_to_switch)
	get_hex = []
	for d in init_datahex:
		get_hex.append(int(ord(d)))
	return get_hex

# function: hex convert to string
def hexlist_to_str(hexlist_to_switch):
	ret_res = "%02x" % (hexlist_to_switch[0])
	for d in hexlist_to_switch[1:]:
		temp = "%02x" % d
		ret_res = ret_res + temp
	return ret_res


# function: get key information
def calc_keyinfo(masterkey, data):
	length = len(data)
	i = 0
	temp_info = []
	while length > 0:
		temp_info += sm4_crypt_ecb(ENCRYPT, masterkey, data[i:i+16])
		i += 16
		length -= 16
	return temp_info
	

# function: calculate MAC
def calc_data_mac(masterkey, init_data, data):
	length = len(data)
	i = 0
	temp_mac = init_data
	while length > 0:
		temp_mac = sm4_crypt_cbc(ENCRYPT, masterkey, temp_mac, data[i:i+16])
		i += 16
		length -= 16
	return temp_mac[0:4]


# function: update master key
def update_master_key(key_update, delivery_en):
	
	# declare global variable
	global defaultkey_Hex
	global cpc_sn
		
	## new master key for update
	new_master_key = key_update
	#print "new_master_key: " + new_master_key + '\n'

	## command head of update master key
	cmd_head = [0x84, 0xD4, 0x01, 0x00 , 0x24]

	#**** get radom
	cmd_get_random = "0084000004"
	random = HFCARD_COMMAND(cmd_get_random)   #get random(4 bytes)
	#print("*** get random: " + str(random) + "\n")

	# if not delivery
	if delivery_en == 0:
		#**** get key information
		data = '13' + '000000' + new_master_key + '800000000000000000000000'
		data_list = str_to_hex(data)
		key_info = calc_keyinfo(defaultkey_Hex, data_list)
		#print_data(key_info, 'key_info: ')
	else:
		#**** delivery key by cpc_sn
		cpc_sn_hex = str_to_hex(cpc_sn + cpc_sn)
		#print_data(cpc_sn_hex, 'cpc_sn_hex: ')
		cpc_sn_invert = [(0xff-d) for d in cpc_sn_hex]
		delivery_factor = cpc_sn_hex + cpc_sn_invert
		#print_data(delivery_factor, "delivery_factor: ")
		new_master_key_hex = str_to_hex(new_master_key)
		delivery_key = sm4_crypt_ecb(ENCRYPT, new_master_key_hex, delivery_factor)
		#print_data(delivery_key, "delivery_key: ")
		delivery_key_str = hexlist_to_str(delivery_key)
		#print 'delivery_key_str' + delivery_key_str + '\n'
		
		#**** get key information
		data = '13' + '000000' + delivery_key_str + '800000000000000000000000'
		data_list = str_to_hex(data)
		key_info = calc_keyinfo(defaultkey_Hex, data_list)
		#print_data(key_info, 'key_info: ')

	#**** get mac
	init = random + '000000000000000000000000'
	init_data = str_to_hex(init)
	data_for_mac = cmd_head + key_info + [0x80] + [0x00]*10
	mac = calc_data_mac(defaultkey_Hex, init_data, data_for_mac)
	#print_data(mac, 'mac: ')
	#print '\n'

	## get command for update master key
	cmd_update_mk_list = cmd_head + key_info + mac
	#print_data(cmd_update_mk_list, "cmd_update_mk_list: ")
	#print '\n'
	cmd_update_mk = hexlist_to_str(cmd_update_mk_list)
	#print('cmd_update_mk:\n' + cmd_update_mk + "\n")

	## execute update master key ##
	pdate_mk = HFCARD_COMMAND(cmd_update_mk) #no return value for success
	return pdate_mk
	#print "\n*** update master key of MF completed ***\n"


# function: update other key but master key
def update_other_key(key_attr, key_update, delivery_en):
	
	# declare global variable
	global defaultkey_Hex
	global cpc_id
	global area_code
	
	## new master key for update
	key_to_update = key_update
	#print "key_to_update: " + key_to_update + '\n'
	
	## command head of update other key
	cmd_head = [0x84, 0xD4, 0x01, 0xFF, 0x24]	

	#**** get radom
	cmd_get_random = "0084000004"
	random = HFCARD_COMMAND(cmd_get_random)   #get random(4 bytes)
	#print("*** random: " + str(random) + "\n")
	
	# if not delivery
	if delivery_en == 0:
		#**** get key information
		data = '13' + key_attr + key_update + '800000000000000000000000'
		data_list = str_to_hex(data)
		key_info = calc_keyinfo(defaultkey_Hex, data_list)
		#print_data(key_info, 'key_info: ')
	elif delivery_en == 1:
		#**** delivery key by cpc_id
		cpc_id_hex = str_to_hex(cpc_id)
		#print_data(cpc_id_hex, 'cpc_id_hex: ')
		cpc_id_invert = [(0xff-d) for d in cpc_id_hex]
		delivery_factor = cpc_id_hex + cpc_id_invert
		#print_data(delivery_factor, "delivery_factor: ")
		key_to_update_hex = str_to_hex(key_to_update)
		delivery_key = sm4_crypt_ecb(ENCRYPT, key_to_update_hex, delivery_factor)
		#print_data(delivery_key, "delivery_key: ")
		delivery_key_str = hexlist_to_str(delivery_key)
		#print 'delivery_key_str ' + delivery_key_str + '\n'

		#**** get key information
		data = '13' + key_attr + delivery_key_str + '800000000000000000000000'
		data_list = str_to_hex(data)
		key_info = calc_keyinfo(defaultkey_Hex, data_list)
		#print_data(key_info, 'key_info: ')
	elif delivery_en == 2:
		#**** delivery key by area_code
		areacode_hex = str_to_hex(area_code + area_code)
		#print_data(cpc_id_hex, 'cpc_id_hex: ')
		areacode_invert = [(0xff-d) for d in areacode_hex]
		delivery_factor = areacode_hex + areacode_invert
		#print_data(delivery_factor, "delivery_factor: ")
		key_to_update_hex = str_to_hex(key_to_update)
		delivery_key_1 = sm4_crypt_ecb(ENCRYPT, key_to_update_hex, delivery_factor)
		#print_data(delivery_key, "delivery_key: ")
		delivery_key_1_str = hexlist_to_str(delivery_key_1)
		#print 'delivery_key_str' + delivery_key_str + '\n'
		
		#**** delivery key by cpc_id
		cpc_id_hex = str_to_hex(cpc_id)
		#print_data(cpc_id_hex, 'cpc_id_hex: ')
		cpc_id_invert = [(0xff-d) for d in cpc_id_hex]
		delivery_factor = cpc_id_hex + cpc_id_invert
		#print_data(delivery_factor, "delivery_factor: ")
		delivery_key = sm4_crypt_ecb(ENCRYPT, delivery_key_1, delivery_factor)
		#print_data(delivery_key, "delivery_key: ")
		delivery_key_str = hexlist_to_str(delivery_key)
		#print 'delivery_key_str' + delivery_key_str + '\n'

		#**** get key information
		data = '13' + key_attr + delivery_key_str + '800000000000000000000000'
		data_list = str_to_hex(data)
		key_info = calc_keyinfo(defaultkey_Hex, data_list)
		#print_data(key_info, 'key_info: ')

	#**** get mac
	init = random + '000000000000000000000000'
	init_data = str_to_hex(init)
	data_for_mac = cmd_head + key_info + [0x80] + [0x00]*10
	mac = calc_data_mac(defaultkey_Hex, init_data, data_for_mac)
	#print_data(mac, 'mac: ')
	#print '\n'

	## get command for update key
	cmd_update_key_list = cmd_head + key_info + mac
	#print_data(cmd_update_key_list, "cmd_update_key_list: ")
	#print '\n'
	cmd_update_key = hexlist_to_str(cmd_update_key_list)
	#print('cmd_update_damk_list:\n' + cmd_update_key + "\n")

	## execute update key *##
	pdate_key = HFCARD_COMMAND(cmd_update_key) #no return value for success
	return pdate_key
	#print "\n*** update other key completed ***\n"


# function: update system information
def update_system_info(info_update):
	
	# declare global variable
	global key_for_sysinfor
	
	## new system information for update
	info_to_update = info_update
	#print "info_to_update: " + info_to_update + '\n'
	
	## command head of update system information
	cmd_head_hex = [0x04, 0xD6, 0x81, 0x00, 0x22] # 0x22 = system_len + mac_len
	
	#**** get radom
	cmd_get_random = "0084000004"
	random = HFCARD_COMMAND(cmd_get_random)   #get random(4 bytes)
	#print("*** random: " + str(random) + "\n")
	
	#**** get mac
	init = random + '000000000000000000000000'
	init_data = str_to_hex(init)
	#print_data(init_data, 'init_data: ')
	sysinfo_for_mac = str_to_hex(info_to_update)
	data_for_mac = cmd_head_hex + sysinfo_for_mac + [0x80] + [0x00]*12	
	
	# @Note: should use DAMK for mac, but now use card master key
	key_for_sysinfor_hex = str_to_hex(key_for_sysinfor)
	mac = calc_data_mac(key_for_sysinfor_hex, init_data, data_for_mac)
	#print_data(mac, 'mac: ')
	#print '\n'
	
	## get command for update system information
	cmd_head = hexlist_to_str(cmd_head_hex)
	mac_str = hexlist_to_str(mac)
	cmd_update_sysinfo = cmd_head + info_to_update + mac_str
	#print('cmd_update_sysinfo:\n' + cmd_update_sysinfo + "\n")

	##* execute update sysinfo *##
	pdate_sysinfo = HFCARD_COMMAND(cmd_update_sysinfo) #no return value for success
	return pdate_sysinfo
	#print "\n*** update sysinfo completed ***\n"



# function: update CPC inter SN
def update_SN(sn_new):
	
	if(len(sn_new) != 8):
		print "The Length of SN is not 4 bytes\n\n"
		return 'error'
		
	ret = HFCARD_COMMAND('80EA030005726f676177')
	if ret != '':
		return ret
		
	ret = HFCARD_COMMAND('80EA010104' + sn_new)
	if ret != '':
		return ret
	return ''



# function: CPC card update 
def cpc_card_update():
	
	# declare global variable
    global defaultkey
    global key_for_sysinfor
    global cpc_sn
    global new_sysinfo
	
	############################ update startup ############################

	# ******************* update DAMK_MF key *******************************	
    DAMK_MF_str = PARAM["DAMK_MF"]
	#DAMK_MF_str = defaultkey
	#*** update DAMK_MF
    ret = update_other_key('010100', DAMK_MF_str, DE_DELIVERY) # do not delivery
    if ret != '': raise Exception("***** DAMK_MF update failed *****")
    print "\n*** update DAMK_MF completed ***\n"

	
	# #******************** update system information ************************
	## key for mac of system information
    key_for_sysinfor = DAMK_MF_str 
	# key_for_sysinfor = DAMK_MF_str
	## get new system information
    sysinfo_for_update = new_sysinfo
    print 'sysinfo_for_update: ' + sysinfo_for_update
    # print "length of sysinfo = " + str(len(sysinfo_for_update) / 2) + '\n'
    ret = update_system_info(sysinfo_for_update)
    if ret != '': raise Exception("***** system_info update failed *****")
    print "\n*** update sysinfo completed ***\n"

	
	#*********************** update master key ****************************
	## get new master key
	#new_master_key = defaultkey
    new_master_key = PARAM["new_master_key"]
    ret = update_master_key(new_master_key, DE_DELIVERY) # do not delivery
    if ret != '': raise Exception("***** master_key update failed *****")
    print "\n*** update master key of MF completed ***\n"


	# ******************** update key of DF01 ******************************
	## Select DF01 ##
    print 'Enter DF01'
    cmd_DF01 = '00A4000002DF01'
    ret = HFCARD_COMMAND(cmd_DF01)
    if ret:
        print "enter DF01 successfully\n"
    else:
        raise Exception("enter DF01 failed")

	#***** update internal authentication key 1 **********
	#inter_auth_key_1 = defaultkey
    inter_auth_key_1 = PARAM["inter_auth_key_1"]
    #inter_auth_key_1 = IK1_rootkey
    inter_auth_key_1_attr = '020100'
    ret = update_other_key(inter_auth_key_1_attr, inter_auth_key_1, PARAM["EN_DELIVERY"])
    if ret != '':
        raise Exception("***** inter_auth_key_1 update failed *****")
    print "\n*** update inter_auth_key_1 completed ***\n"

	
	#***** update internal authentication key 2 **********
    #inter_auth_key_2 = IK1_rootkey
    inter_auth_key_2 = inter_auth_key_1 
    inter_auth_key_2_attr = '020200'	
    ret = update_other_key(inter_auth_key_2_attr, inter_auth_key_2, PARAM["EN_DELIVERY"])
    if ret != '':
        raise Exception("***** inter_auth_key_2 update failed *****")
    print "\n*** update inter_auth_key_2 completed ***\n"


	#***** update external authentication key 1 **********
    #exter_auth_key_1 = init_defaultkey
    exter_auth_key_1 = PARAM["exter_auth_key_1"]
    exter_auth_key_1_attr = '000100'
    ret = update_other_key(exter_auth_key_1_attr, exter_auth_key_1, PARAM["EN_DELIVERY"])
    if ret != '':
        raise Exception("***** exter_auth_key_1 update failed *****")
    print "\n*** update exter_auth_key_1 completed ***\n"


	#***** update external authentication key 2 **********
    #exter_auth_key_2 = init_defaultkey
    exter_auth_key_2 = PARAM["exter_auth_key_2"]
    exter_auth_key_2_attr = '000200'
    ret = update_other_key(exter_auth_key_2_attr, exter_auth_key_2, PARAM["EN_DELIVERY"])
    if ret != '':
        raise Exception("***** exter_auth_key_2 update failed *****")
    print "\n*** update exter_auth_key_2 completed ***\n"


	#***** update external authentication key 3 ********** #### ret 6A 88: No key data
    exter_auth_key_3 = exter_auth_key_1 
    exter_auth_key_3_attr = '000300'
    ret = update_other_key(exter_auth_key_3_attr, exter_auth_key_3, PARAM["EN_DELIVERY"])
    if ret != '':
        raise Exception("***** exter_auth_key_3 update failed *****")
    print "\n*** update exter_auth_key_3 completed ***\n"


	#***** update external authentication key 4 ********** #### ret 6A 88: No key data
    exter_auth_key_4 = exter_auth_key_2 
    exter_auth_key_4_attr = '000400'
    ret = update_other_key(exter_auth_key_4_attr, exter_auth_key_4, PARAM["EN_DELIVERY"])
    if ret != '':
        raise Exception("***** exter_auth_key_4 update failed *****")
    print "\n*** update exter_auth_key_4 completed ***\n"
		

	#************** update DAMK_DF01 key *************	
    DAMK_DF01_str = PARAM["DAMK_DF01"]
	#DAMK_DF01_str = defaultkey
	#*** update DAMK_DF01
    ret = update_other_key('010100', DAMK_DF01_str, DE_DELIVERY) # do not delivery
    if ret != '':
        raise Exception("***** DAMK of DF01 update failed *****")
    print "\n*** update DAMK of DF01 completed ***\n"

	
	# ***** update master key *************
	## get new master key
    new_master_df01 =  PARAM["masterKey_df01"]
	#new_master_key = defaultkey
    ret = update_master_key(new_master_df01, DE_DELIVERY) # do not delivery
    if ret != '':
        raise Exception("***** master key of DF01 update failed *****")
    print "\n*** update master key of DF01 completed ***\n"


# esam filesystem recreate
def cpc_esam_recreate():

    # declare global variable
    global defaultkey
    global key_for_sysinfor
		
   #******************* # erease file ************************************* ####
    ret = HFCARD_COMMAND('80EA030005726F676177') # 80EA030005726F676177
    if ret != '':
        raise Exception('*** HF_CMD run failed ***')
    ret = HFCARD_COMMAND('E5ED000000') # E5ED000000
    if ret != '':
        raise Exception('*** HF_CMD run failed ***')
		
	#************************** create MF ******************************** ####
    ret = HFCARD_COMMAND('80E03F000D18FFFFAAAAFFFFFFFFFFFFFFFF') # 80E03F000D18FFFFAAAAFFFFFFFFFFFFFFFF
    if ret != '':
        raise Exception('*** HF_CMD run failed ***')
	
	#************************** create key file ******************************* ####
    ret = HFCARD_COMMAND('80E00000071F003000AAFFFF') # 80E00000071F003000AAFFFF
    if ret != '':
        raise Exception('*** HF_CMD run failed ***')

    #************************** load master key ******************************* ####
    cmd_load_mk = '80D4000013000000' + defaultkey
    ret = HFCARD_COMMAND(cmd_load_mk) # 80D4000013000000 00000000000000000000000000000000
    if ret != '':
        raise Exception('*** HF_CMD run failed ***')

	#************************** load DAMK_MF ****************************** ####
    DAMK_MF_str = defaultkey
	#*** update DAMK_MF
    ret = update_other_key('010100', DAMK_MF_str, DE_DELIVERY) # do not delivery
    if ret != '':
        raise Exception("***** DAMK_MF load failed *****")

    #************************** create EF01_MF ****************************** ####
    ret = HFCARD_COMMAND('80E0EF010788001EF0F0FFFE') # 80E0EF010788001EF0F0FFFE
    if ret != '':
        raise Exception('*** HF_CMD run failed ***')
	
	#************************** create EF02_MF ***************************** ####
    ret = HFCARD_COMMAND('80E0EF0207080040F0F0FFFF') # 80E0EF0207080040F0F0FFFF
    if ret != '':
        raise Exception('*** HF_CMD run failed ***')

    #************************** create EF03_MF ****************************** ####
    ret = HFCARD_COMMAND('80E0EF0307880080F0F0FFFE') # 80E0EF0307880080F0F0FFFE
    if ret != '':
        raise Exception('*** HF_CMD run failed ***')

    # #******************** update system information ************************ ###
    key_for_sysinfor = defaultkey
	## get new system information
    sysinfo_for_update = new_sysinfo
    #print 'sysinfo_for_update: ' + sysinfo_for_update
    ret = update_system_info(sysinfo_for_update)
    if ret != '':
        raise Exception("***** system_info update failed *****")

    #************************** create DF01 ******************************* ####
    ret = HFCARD_COMMAND('80E0DF0111182800AAAAFFFFFFA00000000386980701') # 80E0DF0111182800AAAAFFFFFFA00000000386980701
    if ret != '':
        raise Exception('*** HF_CMD run failed ***')

    #************************** create key file ****************************** ####
    ret = HFCARD_COMMAND('80E00000071F020000AAFFFF') # 80E00000071F020000AAFFFF
    if ret != '':
        raise Exception('*** HF_CMD run failed ***')

	#************************** load DAMK_DF01 ******************************* ####
    DAMK_DF01_str = defaultkey
    ret = update_other_key('010100', DAMK_DF01_str, DE_DELIVERY) # do not delivery
    if ret != '':
        raise Exception("***** DAMK of DF01 load failed *****")
	
	#************************** load MK_DF01 ******************************* ####
    new_master_key = defaultkey
    ret = update_master_key(new_master_key, DE_DELIVERY) # do not delivery
    if ret != '':
        raise Exception("***** master key of DF01 load failed *****")
    
	#************************** Create file_DF01 ***************************** ####
	# create EF01_DF01
    HFCARD_COMMAND('80E0EF0107080080F011FFFF') # 80E0EF010708 0080 F011FFFF
	# create EF02_DF01
    HFCARD_COMMAND('80E0EF0207080200F041FFFF') # 80E0EF020708 0200 F041FFFF
	# create EF03_DF01
    HFCARD_COMMAND('80E0EF0307080200F0F0FFFF') # 80E0EF030708 0200 F0F0FFFF
	# create EF04_DF01
    HFCARD_COMMAND('80E0EF0407080200F041FFFF') # 80E0EF040708 0200 F041FFFF
	# create EF05_DF01
    HFCARD_COMMAND('80E0EF0507880200F0F0FFFE') # 80E0EF050788 0200 F0F0FFFE
	# create EF06_DF01
    HFCARD_COMMAND('80E0EF0607080080F0F0FFFF') # 80E0EF060708 0080 F0F0FFFF
	# create EF07_DF01
    HFCARD_COMMAND('80E0EF07070A140AF0F0FFFF') # 80E0EF07070A140AF0F0FFFF
	# create EF08_DF01
    HFCARD_COMMAND('80E0EF08078A140AF0F0FFFE') # 80E0EF08078A140AF0F0FFFE
	# create EF09_DF01
    HFCARD_COMMAND('80E0EF09070A140AF011FFFF') # 80E0EF09070A140AF011FFFF
	# create EF0A_DF01
    HFCARD_COMMAND('80E0EF0A070A140AF041FFFF') # 80E0EF0A070A140AF041FFFF

	#************************** update internal authentication key 1 ********** ####
    inter_auth_key_1 = defaultkey
    inter_auth_key_1_attr = '020100'
    ret = update_other_key(inter_auth_key_1_attr, inter_auth_key_1, EN_DELIVERY_L1)
    if ret != '':
        raise Exception("***** inter_auth_key_1 update failed *****")
	
	#************************** update internal authentication key 2 ********** ####
    inter_auth_key_2 = defaultkey
    inter_auth_key_2_attr = '020200'	
    ret = update_other_key(inter_auth_key_2_attr, inter_auth_key_2, EN_DELIVERY_L1)
    if ret != '':
        raise Exception("***** inter_auth_key_2 update failed *****")

	#************************** update external authentication key 1 ********** ####
    exter_auth_key_1 = defaultkey
    exter_auth_key_1_attr = '000100'
    ret = update_other_key(exter_auth_key_1_attr, exter_auth_key_1, EN_DELIVERY_L1)
    if ret != '':
        raise Exception("***** exter_auth_key_1 update failed *****")

	#************************** update external authentication key 2 ********** ####
    exter_auth_key_2 = defaultkey
    exter_auth_key_2_attr = '000200'
    ret = update_other_key(exter_auth_key_2_attr, exter_auth_key_2, EN_DELIVERY_L1)
    if ret != '':
        raise Exception("***** exter_auth_key_2 update failed *****")

	#************************** update external authentication key 3 ********** #### 
    exter_auth_key_3 = defaultkey
    exter_auth_key_3_attr = '000300'
    ret = update_other_key(exter_auth_key_3_attr, exter_auth_key_3, EN_DELIVERY_L1)
    if ret != '':
        raise Exception("***** exter_auth_key_3 update failed *****")

	#************************** update external authentication key 4 ********** #### 
    exter_auth_key_4 = defaultkey
    exter_auth_key_4_attr = '000400'
    ret = update_other_key(exter_auth_key_4_attr, exter_auth_key_4, EN_DELIVERY_L1)
    if ret != '':
        raise Exception("***** exter_auth_key_4 update failed *****")
			



# main of cpc update to startup
def cpc_update_startup(input_defaultkey, delivery_or_not, input_issue_info, input_cpc_id = ''):
	
	# declare global variable
    global defaultkey
    global defaultkey_Hex
    global cpc_sn
    global cpc_id
    global area_code
    global new_sysinfo
	
	
	# judge the length of default master key
    len_key = len(input_defaultkey) / 2
    if len_key != 16:
        print 'Length of defaultkey error'
        return
	
	# judge the length of issue_info
    if input_issue_info != '':		
        len_id = len(input_issue_info) / 2
        if len_id != 8:
            print 'Length of ISSUE_INFO error'
            return	
	
	# judge the length of CPC_ID
    if input_cpc_id != '':			
        len_id = len(input_cpc_id) / 2
        if len_id != 8:
            print 'Length of CPC_ID error'
            return	

	#**** get CPC SN
    cmd_get_SN = "80F6000304"
    cpc_sn = HFCARD_COMMAND(cmd_get_SN)
    print "CPC_SN: " + cpc_sn + "\n"

	# get default master key	
    if delivery_or_not == 0:
        defaultkey = input_defaultkey
        defaultkey_Hex = str_to_hex(defaultkey)	
    else:
        input_defaultkey_Hex = str_to_hex(input_defaultkey)		
        delivery_factor_str = cpc_sn + cpc_sn	
        delivery_factor_1 = str_to_hex(delivery_factor_str)
        delivery_factor_2 = [(0xff-d) for d in delivery_factor_1]
        delivery_factor = delivery_factor_1 + delivery_factor_2
        defaultkey_Hex = sm4_crypt_ecb(ENCRYPT, input_defaultkey_Hex, delivery_factor)
        defaultkey = hexlist_to_str(defaultkey_Hex)
	
	##**** get current issue_info and CPC ID
    # cmd_get_sysinfo = "00b081001e"
    # get_sysinfo = HFCARD_COMMAND(cmd_get_sysinfo)
    get_sysinfo = 'C9CFBAA3310100013101000000000001' + 'FFFFFFFFFFFFFFFFFFFFFFFFFFFF'  #********************** default sysinfo
    print "get_sysinfo: " + get_sysinfo + "\n"
    current_issue_info = get_sysinfo[0:16]
    print "current_issue_info: " + current_issue_info + '\n'
    current_cpc_id = get_sysinfo[16:32]
    print "current_cpc_id: " + current_cpc_id + '\n'
	
    get_sysinfo = get_sysinfo[0:32] + '162018010120501231' + get_sysinfo[50:] # version, start date --> end date 
	
	# if not update issue_info
    if input_issue_info == '':
        new_sysinfo = get_sysinfo		
    else:
		#*** get new CPC ID
        new_issue_info = input_issue_info
        print "new_issue_info: " + new_issue_info + '\n'
        new_sysinfo = new_issue_info + get_sysinfo[16:]
	
	# if not update CPC_ID
    if input_cpc_id == '':
        new_cpc_id = current_cpc_id
    else:
		#*** get new CPC ID
        new_cpc_id = input_cpc_id
        print "new_cpc_id: " + new_cpc_id + '\n'
        new_sysinfo = new_sysinfo[0:16] + new_cpc_id + new_sysinfo[32:]				
	
	# area_code
    area_code = new_sysinfo[0:8]
	# cpc_id
    cpc_id = new_cpc_id	
	
	##*** excute cpc_esam erease
    cpc_esam_recreate()
	
    print "\n\n************************* start to update cpc keys *************************\n\n"
	
    time.sleep(0.2)

    activeEsam()

	##*** excute cpc update
    cpc_card_update()

    # update_SN('11223344') # update CPC_SN
	
    # HFCARD_COMMAND('00a40000023f00')
    # cmd_get_sysinfo = "00b081001e"
    # after_system = HFCARD_COMMAND(cmd_get_sysinfo)
    # after_new_cpcid = after_system[16:32]
    # if after_new_cpcid != cpc_id:
        # print "\n*********** cpc ESAM init and update failed ***********\n"
        # while True:
            # None

