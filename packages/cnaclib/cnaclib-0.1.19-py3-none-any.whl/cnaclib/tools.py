import os
from datetime import datetime
from dateutil import relativedelta
import pandas as pd

##########################################################################################################################################
#                                                       TOOLS
##########################################################################################################################################


def listeCodewils():
    Codewils=[]
    for n in range(1,10):
        Codewils.append("0"+str(n))
    for n in range(10,59):
        Codewils.append(str(n))
    return Codewils


def Codewil(wilaya, langue):
    if langue ==0: # Français

        if wilaya.upper() == "ALGER":
            Codewil = "16"
        elif wilaya.upper() == "JIJEL":
            Codewil = "18"
        elif  wilaya.upper() == "SKIKDA":
            Codewil = "21"
        elif wilaya.upper() == "CONSTANTINE":
            Codewil = "25"
        elif wilaya.upper() == "ANNABA":
            Codewil = "23"
        elif wilaya.upper() == "GUELMA":
            Codewil = "24"
        elif wilaya.upper() == "EL TARF" or wilaya.upper() == "EL TAREF" or wilaya.upper() == "EL-TAREF":
            Codewil = "36"
        elif wilaya.upper() == "CHLEF":
            Codewil = "02"
        elif wilaya.upper() == "BÉJAIA" or wilaya.upper() == "BEJAIA" or wilaya.upper() == "BÉJAÏA":
            Codewil = "06"
        elif wilaya.upper() == "BLIDA":
            Codewil = "09"
        elif wilaya.upper() == "TIZI OUZOU" or wilaya.upper() == "TIZI-OUZOU":
            Codewil = "15"
        elif wilaya.upper() == "BOUMERDES":
            Codewil = "35"
        elif wilaya.upper() == "MOSTAGHANEM" or wilaya.upper() == "MOSTAGANEM":
            Codewil = "27" 
        elif wilaya.upper() == "ORAN":
            Codewil = "31"
        elif wilaya.upper() == "MASCARA":
            Codewil = "29"
        elif wilaya.upper() == "AIN TEMOUCHENT" or wilaya.upper() == "AIN-TEMOUCHENT":
            Codewil = "46"
        elif wilaya.upper() == "AIN DEFLA" or wilaya.upper() == "AIN-DEFLA":
            Codewil ="44"
        elif wilaya.upper() == "TIPAZA":
            Codewil = "42"
        elif wilaya.upper() == "RELIZANE":
            Codewil = "48"
        elif wilaya.upper() == "TEBESSA":
            Codewil = "12"
        elif wilaya.upper() == "OUM EL BOUAGHI" or wilaya.upper() == "OUM-EL-BOUAGHI" or wilaya.upper() == "OUM EL-BOUAGHI":
            Codewil = "04"
        elif wilaya.upper() == "KHENCHELA" or wilaya.upper() == "KHENCHLA":
            Codewil = "40"
        elif wilaya.upper() == "BATNA":
            Codewil = "05"
        elif wilaya.upper() == "SETIF" or wilaya.upper() == "SÉTIF":
            Codewil = "19"
        elif wilaya.upper() == "BORDJ BOUARRERIDJ" or wilaya.upper() == "BORDJ BOU ARRERIDJ" or wilaya.upper() == "BORDJ BOU-ARRERIDJ":
            Codewil = "34"
        elif wilaya.upper() == "M'SILA" or wilaya.upper() == "MSILA":
            Codewil = "28"
        elif wilaya.upper() == "DJELFA":
            Codewil = "17"
        elif wilaya.upper() == "MILA":
            Codewil = "43"
        elif wilaya.upper() == "TLEMCEN":
            Codewil = "13"
        elif wilaya.upper() == "SIDI BEL ABBES" or wilaya.upper() == "SIDI BELABES" or wilaya.upper() == "SIDI BEL-ABBES":
            Codewil = "22"
        elif wilaya.upper() == "TISSEMSILT":
            Codewil = "38"
        elif wilaya.upper() == "TIARET":
            Codewil = "14"
        elif wilaya.upper() == "SAIDA":
            Codewil = "20"
        elif wilaya.upper() == "EL BAYADH" or wilaya.upper() == "EL-BAYADH":
            Codewil = "32"
        elif wilaya.upper() == "BOUIRA":
            Codewil = "10"
        elif wilaya.upper() == "SOUK AHRAS" or wilaya.upper() == "SOUK-AHRAS" or wilaya.upper() == "SOUKAHRAS":
            Codewil = "41"
        elif wilaya.upper() == "MEDEA" or wilaya.upper() == "MÉDEA":
            Codewil = "26"
        elif wilaya.upper() == "NAAMA" or wilaya.upper() == "NAÂMA":
            Codewil = "45"
        elif wilaya.upper() == "BISKRA":
            Codewil = "07"
        elif wilaya.upper() == "EL OUED" or wilaya.upper() == "EL-OUED":
            Codewil = "39"
        elif wilaya.upper() == "OUARGLA":
            Codewil = "30"
        elif wilaya.upper() == "GHARDAIA":
            Codewil = "47"
        elif wilaya.upper() == "BECHAR" or wilaya.upper() == "BÉCHAR":
            Codewil = "08"
        elif wilaya.upper() == "LAGHOUAT":
            Codewil = "03"
        elif wilaya.upper() == "ILLIZI":
            Codewil = "33"
        elif wilaya.upper() == "TAMANRASSET" or wilaya.upper() == "TAMANRASSET":
            Codewil = "11"
        elif wilaya.upper() == "TINDOUF":
            Codewil = "37"
        elif wilaya.upper() == "ADRAR":
            Codewil = "01"
        
        elif wilaya.upper() == "TIMIMOUN":
            Codewil = "49"
        elif wilaya.upper() == "BORDJ BAJI MOKHTAR":
            Codewil = "50"
        elif wilaya.upper() == "OULED DJELLAL":
            Codewil = "51"
        elif wilaya.upper() == "BENI ABBES":
            Codewil = "52"
        elif wilaya.upper() == "IN SALAH":
            Codewil = "53"
        elif wilaya.upper() == "IN GUEZZAM":
            Codewil = "54"
        elif wilaya.upper() == "TOUGGOURT":
            Codewil = "55"
        elif wilaya.upper() == "DJANET":
            Codewil = "56"
        elif wilaya.upper() == "EL MEGHAIER":
            Codewil = "57"
        elif wilaya.upper() == "EL MENIAA":
            Codewil = "58"
    
    if langue ==1: # Arabe

        if wilaya == "الجزائر":
            Codewil = "16"
        elif wilaya == "عنابة":
            Codewil = "23"
        elif wilaya == "أدرار":
            Codewil = "01"
        elif wilaya == "الشلف":
            Codewil = "02"
        elif wilaya == "الأغواط":
            Codewil = "04"
        elif wilaya == "أم البواقي":
            Codewil = "04" 
        elif wilaya == "باتنة":
            Codewil = "05" 
        elif wilaya == "بجاية":
            Codewil = "06" 
        elif wilaya == "بسكرة":
            Codewil = "07" 
        elif wilaya == "بشار":
            Codewil = "08" 
        elif wilaya == "البليدة":
            Codewil = "09" 
        elif wilaya == "البويرة":
            Codewil = "10" 
        elif wilaya == "تمنراست":
            Codewil = "11" 
        elif wilaya == "تبسة":
            Codewil = "12" 
        elif wilaya == "تلمسان":
            Codewil = "13" 
        elif wilaya == "تيارت":
            Codewil = "14" 
        elif wilaya == "تيزى وزو":
            Codewil = "16" 
        elif wilaya == "الجلفة":
            Codewil = "17" 
        elif wilaya == "جيجل":
            Codewil = "18" 
        elif wilaya == "سطيف":
            Codewil = "19" 
        elif wilaya == "سعيدة":
            Codewil = "20" 
        elif wilaya == "سكيكدة":
            Codewil = "21" 
        elif wilaya == "سيدي بلعباس":
             Codewil = "22" 
        elif wilaya == "عنابة":
            Codewil = "23" 
        elif wilaya == "قالمة":
            Codewil = "24"
        elif wilaya == "قسنطينة":
            Codewil = "25" 
        elif wilaya == "المدية":
            Codewil = "26" 
        elif wilaya == "مستغانم":
            Codewil = "27" 
        elif wilaya == "المسيلة":
            Codewil = "28" 
        elif wilaya == "معسكر":
            Codewil = "29" 
        elif wilaya == "ورقلة":
            Codewil = "30" 
        elif wilaya == "وهران":
            Codewil = "31" 
        elif wilaya == "البيض":
            Codewil = "32" 
        elif wilaya == "ايليزى":
            Codewil = "33" 
        elif wilaya == "برج بوعريرج":
            Codewil = "34" 
        elif wilaya == "بومرداس":
            Codewil = "35" 
        elif wilaya == "الطارف":
             Codewil = "36" 
        elif wilaya == "تندوف":
             Codewil = "37" 
        elif wilaya == "تيسمسيلت":
             Codewil = "38" 
        elif wilaya == "الوادى":
            Codewil = "39" 
        elif wilaya == "خنشلة":
            Codewil = "40" 
        elif wilaya == "سوق أهراس":
            Codewil = "41" 
        elif wilaya == "تيبازة":
            Codewil = "42" 
        elif wilaya == "ميلة":
            Codewil = "43" 
        elif wilaya == "عين الدفلى":
            Codewil = "44" 
        elif wilaya == "النعامة":
            Codewil = "45" 
        elif wilaya == "عين تموشنت":
            Codewil = "46" 
        elif wilaya == "غرداية":
            Codewil = "47" 
        elif wilaya =="غليزان":
            Codewil = "48"
        elif wilaya == "تيميمون":
            Codewil = "49"
        elif wilaya == "برج باجى مختار":
            Codewil = "50"
        elif wilaya == "أولاد جلال":
            Codewil = "51"
        elif wilaya == "بنى عباس":
            Codewil = "52"
        elif wilaya == "ان صالح":
             Codewil = "53"
        elif wilaya == "أن قزام":
            Codewil = "54"
        elif wilaya == "توقرت":
            Codewil = "55"
        elif wilaya == "جانت":
            Codewil = "56"
        elif wilaya == "المغير":
            Codewil = "57"
        elif wilaya == "المنيعة":
            Codewil = "58"

    return Codewil

def NomWil(Codewil, langue) :
    if langue == 0 : #Fraçais

        if Codewil == '16':
            NomWil = 'ALGER'
        elif Codewil == '23' :
            NomWil = 'ANNABA'
        elif Codewil == '01' :
            NomWil = 'ADRAR'
        elif Codewil == '02' :
            NomWil = 'CHLEF'
        elif Codewil == '03' :
            NomWil = 'LAGHOUAT'
        elif Codewil == '04' :
            NomWil = 'OUM EL BOUAGHI'
        elif Codewil == '05' :
            NomWil = 'BATNA'
        elif Codewil == '06' :
            NomWil = 'BEJAIA'
        elif Codewil == '07' :
            NomWil = 'BISKRA'
        elif Codewil == '08' :
            NomWil = 'BECHAR'
        elif Codewil == '09' :
            NomWil = 'BLIDA'
        elif Codewil == '10' :
            NomWil = 'BOUIRA'
        elif Codewil == '11' :
            NomWil = 'TAMANRASSET'
        elif Codewil == '12' :
            NomWil = 'TEBESSA'
        elif Codewil == '13' :
            NomWil = 'TLEMCEN'
        elif Codewil == '14' :
            NomWil = 'TIARET'
        elif Codewil == '15' :
            NomWil = 'TIZI-OUZOU'
        elif Codewil == '17' :
            NomWil = 'DJELFA'
        elif Codewil == '18' :
            NomWil = 'JIJEL'
        elif Codewil == '19' :
            NomWil = 'SETIF'
        elif Codewil == '20' :
            NomWil = 'SAIDA'
        elif Codewil == '21' :
            NomWil = 'SKIKDA'
        elif Codewil == '22' :
            NomWil = 'SIDI BELABES'
        elif Codewil == '23' :
            NomWil = 'ANNABA'
        elif Codewil == '24' :
            NomWil = 'GUELMA'
        elif Codewil == '25' :
            NomWil = 'CONSTANTINE'
        elif Codewil == '26' :
            NomWil = 'MEDEA'
        elif Codewil == '27' :
            NomWil = 'MOSTAGANEM'
        elif Codewil == '28' :
            NomWil = "M'SILA"
        elif Codewil == '29' :
            NomWil = 'MASCARA'
        elif Codewil == '30' :
            NomWil = 'OUARGLA'
        elif Codewil == '31' :
            NomWil = 'ORAN'
        elif Codewil == '32' :
            NomWil = 'EL BAYADH'
        elif Codewil == '33' :
            NomWil = 'ILLIZI'
        elif Codewil == '34' :
            NomWil = 'BORDJ BOUARRERIDJ'
        elif Codewil == '35' :
            NomWil = 'BOUMERDES'
        elif Codewil == '36' :
            NomWil = 'EL TARF'
        elif Codewil == '37' :
            NomWil = 'TINDOUF'
        elif Codewil == '38' :
            NomWil = 'TISSEMSILT'
        elif Codewil == '39' :
            NomWil = 'EL OUED'
        elif Codewil == '40' :
            NomWil = 'KHENCHELA'
        elif Codewil == '41' :
            NomWil = 'SOUK AHRAS'
        elif Codewil == '42' :
            NomWil = 'TIPAZA'
        elif Codewil == '43' :
            NomWil = 'MILA'
        elif Codewil == '44' :
            NomWil = 'AIN DEFLA'
        elif Codewil == '45' :
            NomWil = 'NAAMA'
        elif Codewil == '46' :
            NomWil = 'AIN TEMOUCHENT'
        elif Codewil == '47' :
            NomWil = 'GHARDAIA'
        elif Codewil == '48' :
            NomWil = 'RELIZANE'
        elif Codewil == "49":
            NomWil = "TIMIMOUN"
        elif Codewil == "50":
            NomWil = "BORDJ BAJI MOKHTAR"
        elif Codewil == "51":
            NomWil = "OULED DJELLAL"
        elif Codewil == "52":
            NomWil = "BENI ABBES"
        elif Codewil == "53":
            NomWil = "IN SALAH"
        elif Codewil == "54":
            NomWil = "IN GUEZZAM"
        elif Codewil == "55":
            NomWil = "TOUGGOURT"
        elif Codewil == "56":
            NomWil = "DJANET"
        elif Codewil == "57":
            NomWil = "EL MEGHAIER"
        elif Codewil == "58":
            NomWil = "EL MENIAA"
    
    if langue == 1 : #Arabe
       
        if Codewil == "16" :
            NomWil = "الجزائر"
        elif Codewil == "23" :
            NomWil = "عنابة"
        elif Codewil == "01" :
            NomWil = "أدرار"
        elif Codewil == "02" :
            NomWil = "الشلف"
        elif Codewil == "03" :
            NomWil = "الأغواط"
        elif Codewil == "04" :
            NomWil = "أم البواقي"
        elif Codewil == "05" :
            NomWil = "باتنة"
        elif Codewil == "06" :
            NomWil = "بجاية"
        elif Codewil == "07" :
            NomWil = "بسكرة"
        elif Codewil == "08" :
            NomWil = "بشار"
        elif Codewil == "09" :
            NomWil = "البليدة"
        elif Codewil == "10" :
            NomWil = "البويرة"
        elif Codewil == "11" :
            NomWil = "تمنراست"
        elif Codewil == "12" :
            NomWil = "تبسة"
        elif Codewil == "13" :
            NomWil = "تلمسان"
        elif Codewil == "14" :
            NomWil = "تيارت"
        elif Codewil == "15" :
             NomWil = "تيزى وزو"
        elif Codewil == "17" :
             NomWil = "الجلفة"
        elif Codewil == "18" :
             NomWil = "جيجل"
        elif Codewil == "19" :
             NomWil = "سطيف"
        elif Codewil == "20" :
             NomWil = "سعيدة"
        elif Codewil == "21" :
             NomWil = "سكيكدة"
        elif Codewil == "22" :
             NomWil = "سيدي بلعباس"
        elif Codewil == "23" :
             NomWil = "عنابة"
        elif Codewil == "24" :
             NomWil = "قالمة"
        elif Codewil == "25" :
             NomWil = "قسنطينة"
        elif Codewil == "26" :
             NomWil = "المدية"
        elif Codewil == "27" :
             NomWil = "مستغانم"
        elif Codewil == "28" :
             NomWil = "المسيلة"
        elif Codewil == "29" :
             NomWil = "معسكر"
        elif Codewil == "30" :
             NomWil = "ورقلة"
        elif Codewil == "31" :
             NomWil = "وهران"
        elif Codewil == "32" :
             NomWil = "البيض"
        elif Codewil == "33" :
             NomWil = "ايليزى"
        elif Codewil == "34" :
             NomWil = "برج بوعريرج"
        elif Codewil == "35" :
             NomWil = "بومرداس"
        elif Codewil == "36" :
             NomWil = "الطارف"
        elif Codewil == "37" :
             NomWil = "تندوف"
        elif Codewil == "38" :
             NomWil = "تيسمسيلت"
        elif Codewil == "39" :
             NomWil = "الوادى"
        elif Codewil == "40" :
             NomWil = "خنشلة"
        elif Codewil == "41" :
             NomWil = "سوق أهراس"
        elif Codewil == "42" :
             NomWil = "تيبازة"
        elif Codewil == "43" :
             NomWil = "ميلة"
        elif Codewil == "44" :
             NomWil = "عين الدفلى"
        elif Codewil == "45" :
             NomWil = "النعامة"
        elif Codewil == "46" :
             NomWil = "عين تموشنت"
        elif Codewil == "47" :
             NomWil = "غرداية"
        elif Codewil == "48" :
             NomWil = "غليزان"
        elif Codewil == "49":
             NomWil = "تيميمون"
        elif Codewil == "50":
             NomWil = "برج باجى مختار"
        elif Codewil == "51":
             NomWil = "أولاد جلال"
        elif Codewil == "52":
             NomWil = "بنى عباس"
        elif Codewil == "53":
             NomWil = "ان صالح"
        elif Codewil == "54":
             NomWil = "أن قزام"
        elif Codewil == "55":
             NomWil = "توقرت"
        elif Codewil == "56":
             NomWil = "جانت"
        elif Codewil == "57":
             NomWil = "المغير"
        elif Codewil == "58":
             NomWil = "المنيعة"
    
    return NomWil


def Region(Wilaya, langue):
    Nord = ['06','02','09','10','13','15','16','18','21','22','23','24','25','26','27','29','31','35','36','41','42','43','44','46','48','02','06','09','10','13','15','16','18','21','22','23','24','25','26','27','29','31','35','36','41','42','43','44','46','48']
    Haut_Plateaux = ['05','04','12','14','17','19','20','28','32','34','38','40','45','04','05','12','14','17','19','20','28','32','34','38','40','45']
    Sud = ['03','01','07','08','11','30','33','37','39','47','49','50','51','52','53','54','55','56','57','58','01','03','07','08','11','30','33','37','39','47','49','50','51','52','53','54','55','56','57','58']
    
    if langue ==0:
        if Codewil(Wilaya, langue) in Nord:
            region = 'Nord'
        elif Codewil(Wilaya, langue) in Haut_Plateaux:
            region = 'Haut-Plateaux'
        else:
            region = 'Sud'
    elif langue ==1:
        if Codewil(Wilaya, langue) in Nord:
            region = 'الشمال'
        elif Codewil(Wilaya, langue) in Haut_Plateaux:
            region = 'الهضاب العليا'
        else:
            region = 'الجنوب'
    return region

def GenererDossiers(langue):
    '''Cette fonction vous permet de créér automatiquement des dossiers qui portent 
       le nom des wilaya en français ou en arabe.   
    '''
    chemin=os.path.dirname("")
    if langue ==0:
        for code in listeCodewils():
            if not os.path.exists(code+'-'+NomWil(code, langue)):
                os.mkdir(chemin+code+'-'+NomWil(code, langue))

    elif langue == 1:
        for code in listeCodewils():
            if not os.path.exists(code+'-'+NomWil(code, langue)):
                os.mkdir(chemin+code+'-'+NomWil(code, langue))


def SNMG(date_saisie):
    date_saisie = datetime.strptime(date_saisie, "%d/%m/%Y").date()

    listeDatesFinStr = ['31/12/1990','30/06/1991','31/03/1992', 
                   '30/04/1997','31/12/1997','31/08/1998',
                   '31/12/2000','31/12/2003','31/12/2006', 
                   '31/12/2009','31/12/2011','31/05/2020', 
                    ]
    dateDebut = datetime.strptime('01/01/1990', "%d/%m/%Y").date()

    listeDatesFin = [datetime.strptime(i, "%d/%m/%Y").date() for i in listeDatesFinStr]

    jourPlus = relativedelta.relativedelta(days=1)
    anneePlus =relativedelta.relativedelta(years=1)
    
    valeurs = [1000.0, 1800.0, 2000.0, 2500.0, 4800.0, 5400.0, 6000.0, 8000.0, 10000.0, 12000.0, 15000.0, 18000.0, 20000.0]
    
    snmg_dict = {
        '0': {"DateDebut":dateDebut,
            "DateFin":listeDatesFin[0],
            "SNMG":valeurs[0]
        }
    }
    
    for index, date  in enumerate(listeDatesFin):

        snmg_dict[str(index+1)] = {
            "DateDebut":date + jourPlus,
            "DateFin":listeDatesFin[index+1],
            "SNMG":valeurs[index+1]
        }

        if index == 10:
            snmg_dict['12'] = {"DateDebut":listeDatesFin[index+1] + jourPlus,
                "DateFin":datetime.today().date()+anneePlus,
                "SNMG":valeurs[12]}      
            break
     
    for dict in snmg_dict:
        debut = snmg_dict[dict].get('DateDebut')
        fin = snmg_dict[dict].get('DateFin')   
        if date_saisie >= debut and date_saisie <= fin:
            snmg = snmg_dict[dict].get('SNMG')
            break
        else:
            snmg = 0
    snmg_tbl = pd.DataFrame(snmg_dict.values(), snmg_dict.keys())
    return snmg, snmg_dict, snmg_tbl





