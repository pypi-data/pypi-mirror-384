# Importer les modules

from datetime import datetime
import pandas as pd
from dateutil import relativedelta
from cnaclib.tools import SNMG

##########################################################################################################################################
#                                                       REGIME ASSURANCE CHOMAGE : SIMULATEUR
##########################################################################################################################################


class RAC:
    '''
    REGIME ASSURANCE CHOMAGE : SIMULATEUR

    Cette Classe en 'python' permet de réaliser des simulations pour le calculs des différents éléments liés au régime d'assurance chômage.
    Elle permet de :
    - Vérifier la condition d'admission relative à l'experience professionnelle;
    - Calculer la durée de prise en charge (DPC);
    - Calculer le montant de la Contribution d'Ouverture de Droits;
    - Récupérer le montant du SNMG en fonction de la date;
    - Calculer les montants d'indemnités en fonction des 04 périodes;
    - Calculer les montants de cotisations de sécurité sociale (part patronale & part salariale );

    Parameters
    ----------

    DateRecrutement : date, 
        C'est de la date de recrutement du salarié chez le dernier employeur.
        Elle doit être exprimé selon le format : dd/mm/yyyy.


    DateCompression : date,
        C'est la de compression du salarié chez le dernier employeur.
        Elle doit être exprimé selon le format : dd/mm/yyyy.

    
    SMM : float,
        C'est le Salaire Mensuel Moyen des 12 derniers mois.
        Il doit être exprimé en DA et concerne la moyenne des salaires soumis à cotisation de sécurité sociale des 12 derniers mois.

    
    Attributes
    ----------

    annee : int,
        C'est la durée d'experience en année;

    mois : int,
        C'est la durée d'experience en mois lorsque la période est inferieure à une année;
    
    jours : int,
        C'est la durée d'experience en jours lorsque la période est inferieure à un mois;

    '''


    def __init__(self, DateRecrutement, DateCompression, SMM):
        self.DateRecrutement = DateRecrutement
        self.DateCompression = DateCompression
        self.SMM = SMM
        self.annee = None
        self.mois = None
        self.jours = None

    def Cal_Durexp(self):
        d1 = datetime.strptime(self.DateCompression, "%d/%m/%Y")
        d2 = datetime.strptime(self.DateRecrutement, "%d/%m/%Y")
        delta = relativedelta.relativedelta(d1, d2)
        self.annee = delta.years
        self.mois = delta.months
        self.jours = delta.days
        
    
    def Verif_admission(self):
        '''
        Verifie les conditions d'admissions relatives a la durée d'experience professionnelle en année, mois et jours.

        Parameters
        ----------
        None.
        
        Returns
        -------
        admission : Une valeur string qui prend 03 possibilites : 
                    "Admis"--> Le salarié remplis les conditions relative a la durée d'experience professionnelle.
                    "Ajourne"--> Il faut verifier si le salarie a cumulé 03 ans de cotisations chez d'autres employeurs.
                    "Non Admis" --> Le salarié n'a pas atteint le minimum de 06 mois de d'experience chez le dernier employeur.
        '''
                       
        if self.annee >= 3:
            admission = "Admis"
        elif self.annee > 0 and self.annee < 3 :  
            admission = "Ajourné"
        elif self.annee < 1 and self.mois >=6:
            admission = "Ajourné"
        else:
            admission = "Non Admis"
        return admission

    def Message_admission(self):
        '''
        Renvoie un message aprés verification des conditions d'admission relatives a la durée d'experience professionnelle en annee, mois et jours.

        Parameters
        ----------
        None.
        
        Returns
        -------
        admission : Un message selon le cas : "Admis", "Ajourne" et "Non admis.
        '''
                       
        if self.annee >= 3:
            message = "Si vous remplissez les conditions prealablement citees et selon votre experience professionnelle calculee, vous pouvez beneficier du Regime Assurance Chomage."
        elif self.annee > 0 and self.annee < 3 :  
            message = "Selon votre duree experience calculee, nous devons verifier si vous avez cumule 03 ans de cotisation a la Securite Sociale."
        elif self.annee < 1 and self.mois >=6:
            message = "Selon votre duree experience calculee, nous devons verifier si vous avez cumule 03 ans de cotisation a la Securite Sociale."
        else:
            message = "Selon votre duree experience calculee, vous ne pouvez pas beneficier du Regime Assurance Chomage."
        return message
    
    def Cal_DateAdmission(self, Mois=1):

        '''
        Calcule une date admission en fonction de la date fournie (dateCompression) et de nombre de mois a rajouter.

        Parameters
        ----------
        Mois : int, default 1.
        Le nombre de mois a rajouter aprés la date de compression.
        
        Returns
        -------
        DateAdmission : Une date d'admission théorique.
        '''
        if self.annee < 3 :
            DateAdmission = datetime(1900,1,1)
        else :
            DateAdmission = datetime.strptime(self.DateCompression, "%d/%m/%Y") + relativedelta.relativedelta(months=Mois)
        return DateAdmission
    
    
    def Cal_DPC(self):
        '''
        Calcule la Durée de Prise en Charge DPC en nombre de mois.

        Parameters
        ----------
        None.
        
        Returns
        -------
        dpc : Durée de prise en charge en nombre de mois.
        '''
        if self.annee < 3 :
            dpc = 0
        elif  self.annee >= 3 :
            dpc = self.annee * 2
            if self.mois == 0 and self.jours == 0:
                dpc += 0
            elif self.mois == 0 and self.jours > 0:
                dpc  += 1
            elif self.mois == 6 and self.jours == 0:
                dpc += 1
            elif self.mois == 6 and self.jours > 0:
                dpc += 2
            elif self.mois > 6:
                dpc += 2
            elif self.mois < 6:
                dpc += 1
                        
            if dpc < 12:
                dpc = 12
            elif dpc > 36:
                dpc = 36
        
        return dpc
    
    def Cal_COD(self): 
        '''
        Calcule le montant de contribution forfetaire d'ouverture de droits mensuelle et totale (COD) à la charge de l'employeur.

        Parameters
        ----------
        None
        
        Returns
        -------
        CODMensuel : COD mensuelle.
        CODTotale : COD Totale à payer par l'employeur.
        '''
        
        if self.annee < 3 :
            CODMensuel = 0.0
            CODTotale = 0.0
            
        elif  self.annee >= 3 and self.annee <18:
            CODMensuel =  0.8 * self.SMM
            CODTotale = (self.annee - 3) * CODMensuel
            if self.mois == 0 and self.jours == 0:
                CODTotale += 0
            elif self.mois == 0 and self.jours > 0:
                CODTotale +=  0.4 * self.SMM
            elif self.mois == 6 and self.jours == 0:
                CODTotale += 0.4 * self.SMM
            elif self.mois == 6 and self.jours > 0:
                CODTotale += 0.8 * self.SMM
            elif self.mois > 6:
                CODTotale +=  0.8 * self.SMM
            elif self.mois < 6:
                CODTotale += 0.4 * self.SMM   
        elif self.annee >=18:
            CODMensuel =  0.8 * self.SMM
            CODTotale = ((18-3) * CODMensuel)

        return CODMensuel, CODTotale

    def Cal_NumPeriode(self, dpc):
        '''
        Renvoi un dictionnaire qui comporte le numero de la période de prise en charge (de 1 a 4) ainsi que les numéros des mois (de 1 a dpc)
        qui appartienne a chaque periode.

        Parameters
        ----------
        dpc : int.
        La durée de prise en charge.
        
        Returns
        -------
        Un dictionnaire {Numero periode : Numero mois}.
        '''
        NumMois = [x for x in range(1, (dpc) + 1)]
        if (dpc/4) - int((dpc/4)) ==0.0:
            NumPeriode = []
            z = int((dpc)/4)
            for m in NumMois:
                if m <= z : 
                    NumPeriode.append("P1")
                elif (m > z and m <= z * 2):
                    NumPeriode.append("P2")
                elif (m > z * 2 and m <= z * 3):
                    NumPeriode.append("P3")
                else:
                    NumPeriode.append("P4")
            #MoisPeriode = {NumMois[x]: NumPeriode[x] for x in range(len (NumMois))}
        elif (dpc/4) - int((dpc/4)) ==0.25:
            NumPeriode = []
            z = int((dpc)/4)
            for m in NumMois:
                if m <= z+1 : 
                    NumPeriode.append("P1")
                elif (m > (z + 1) and m <= (z * 2)+1):
                    NumPeriode.append("P2")
                elif (m > z * 2 and m <= (z * 3)+1):
                    NumPeriode.append("P3")
                else:
                    NumPeriode.append("P4")
            #MoisPeriode = {NumMois[x]: NumPeriode[x] for x in range(len (NumMois))}
        elif (dpc/4) - int((dpc/4)) == 0.5:
            NumPeriode = []
            z = int((dpc)/4)
            for m in NumMois:
                if m <= z+1 : 
                    NumPeriode.append("P1")
                elif (m > z+1 and m <= (z * 2)+2):
                    NumPeriode.append("P2")
                elif (m > (z * 2)+2 and m <= (z * 3)+2):
                    NumPeriode.append("P3")
                else:
                    NumPeriode.append("P4")
        
        elif (dpc/4) - int((dpc/4)) == 0.75:
            NumPeriode = []
            z = int((dpc)/4)
            for m in NumMois:
                if m <= z+1 : 
                    NumPeriode.append("P1")
                elif (m > z+1 and m <= (z * 2)+2):
                    NumPeriode.append("P2")
                elif (m > (z * 2)+2 and m <= (z * 3)+3):
                    NumPeriode.append("P3")
                else:
                    NumPeriode.append("P4")
        MoisPeriode = {NumMois[x]: NumPeriode[x] for x in range(len (NumMois))}  
        return MoisPeriode

    def Cal_SNMG(self, Date):
        '''
        Renvoie le Salaire National Minimum Garanti en fonction de la date fournie.

        Parameters
        ----------
        Date : str.
        Une date au format texte --> "dd/mm/yyyy".
        
        Returns
        -------
        Le Salaire National Minimum Garanti.
        '''
        return SNMG(Date)[0]


    def Cal_SalRef(self, snmg):
        '''
        Calcul le Salaire de référence qui est calculé sur la base du Salaire mensuel moyen et le Salaire National Minimum Garanti.


        Parameters
        ----------
        snmg : float.
        Le Salaire National Minimum Garanti.
        
        Returns
        -------
        Le Salaire de référence.
        '''
        if self.annee < 3 :
            SalRef = 0.0
        else:
            SalRef = (float(snmg) + float(self.SMM)) / 2
        return SalRef
 
    
    def Cal_Indemnite(self, MoisPeriode, snmg, SalRef, DateAdmission, dpc): 
        
        '''
        Calcul plusieurs élements relatives au calendrier des indemnités à percevoir par le salarié tel que :
         - Dates : les dates de paiement des indemnités en focntion de la date d'admission théorique.
         - Indemnites Brutes : Les montants des indemnités brutes.
         - Indemnites Netes : Les montants des indemnités nettes.
         - Part Patronale : Les montants de la part patronale à la charge de la CNAC


        Parameters
        ----------
        - MoisPeriode : dict, 
            Un dictionnaire {Numero periode : Numero mois}.
        - snmg :  float,
            Le Salaire National Minimum Garanti.
        - SalRef : float,
            Le salaire de référence.
        - DateAdmission : str.
            La date admission théorique.
        
        Returns
        -------
        - DateMois :les dates de paiement des indemnités en focntion de la date d'admission théorique.
        - IndemniteBrut : Les montants des indemnités brutes.
        - IndemniteNet : Les montants des indemnités nettes.
        - PartPatronale : Les montants de la part patronale à la charge de la CNAC.
        '''
        
        IndemniteBrut = []
        IndemniteNet = []
        PartPatronale = []
        DateMois = []
        
        for m in MoisPeriode:
            nextmois = DateAdmission + relativedelta.relativedelta(months=m)
            DateMois.append(nextmois)
        
        for m in MoisPeriode:
            if (MoisPeriode[m] == "P1"  and m <= int(dpc/4)): 
                if 1 * SalRef < 0.75 * snmg:
                    IndemniteBrut.append(0.75 * snmg)
                elif 1 * SalRef > 3 * snmg :
                    IndemniteBrut.append(3 * snmg)
                else : 
                    IndemniteBrut.append(1 * SalRef)
            
            if (MoisPeriode[m] == "P1"  and m > int(dpc/4)): 
                if ((1 * SalRef * 0.25) + (0.8 * SalRef * 0.75)) < 0.75 * snmg:
                    IndemniteBrut.append(0.75 * snmg)
                elif ((1 * SalRef * 0.25) + (0.8 * SalRef * 0.75))  > 3 * snmg :
                    IndemniteBrut.append(3 * snmg)
                else : 
                    IndemniteBrut.append(((1 * SalRef * 0.25) + (0.8 * SalRef * 0.75)) )
            
            if (MoisPeriode[m] == "P2" and m <= (int(dpc/4)*2)+1):
                if 0.8 * SalRef < 0.75 * snmg:
                    IndemniteBrut.append(0.75 * snmg)
                elif 0.8 * SalRef > 3 * snmg :
                    IndemniteBrut.append(3 * snmg)
                else : 
                    IndemniteBrut.append(0.8 * SalRef)

            if (MoisPeriode[m] == "P2" and m > (int(dpc/4)*2)+1):
                if ((0.8 * SalRef * 0.5) + (0.6 * SalRef * 0.5)) < 0.75 * snmg:
                    IndemniteBrut.append(0.75 * snmg)
                elif ((0.8 * SalRef * 0.5) + (0.6 * SalRef * 0.5))  > 3 * snmg :
                    IndemniteBrut.append(3 * snmg)
                else : 
                    IndemniteBrut.append(((0.8 * SalRef * 0.5) + (0.6 * SalRef * 0.5)) )

            if (MoisPeriode[m] == "P3" and m <= (int(dpc/4)*3)+2):
                if 0.6 * SalRef < 0.75 * snmg:
                    IndemniteBrut.append(0.75 * snmg)
                elif 0.6 * SalRef > 3 * snmg :
                    IndemniteBrut.append(3 * snmg)
                else : 
                    IndemniteBrut.append(0.6 * SalRef)
            if (MoisPeriode[m] == "P3" and m > (int(dpc/4)*3)+2):
                if ((0.6 * SalRef * 0.75) + (0.5 * SalRef * 0.25)) < 0.75 * snmg:
                    IndemniteBrut.append(0.75 * snmg)
                elif ((0.6 * SalRef * 0.75) + (0.5 * SalRef * 0.25))  > 3 * snmg :
                    IndemniteBrut.append(3 * snmg)
                else : 
                    IndemniteBrut.append(((0.6 * SalRef * 0.75) + (0.5 * SalRef * 0.25)) )
            
            if MoisPeriode[m] == "P4":
                if 0.5 * SalRef < 0.75 * snmg:
                    IndemniteBrut.append(0.75 * snmg)
                elif 0.5 * SalRef > 3 * snmg :
                    IndemniteBrut.append(3 * snmg)
                else : 
                    IndemniteBrut.append(0.5 * SalRef)
        
        for ind in IndemniteBrut:
            PartPatronale.append(snmg * 0.15)
            if ind <= snmg :
                IndemniteNet.append(ind)
            else:
                IndemniteNet.append(ind - (ind*0.085))
        
        return DateMois, IndemniteBrut, IndemniteNet, PartPatronale

    def tableaux_Indemnites(self, MoisPeriode, DateMois, IndemniteBrut, IndemniteNet, PartPatronale):
        '''
        Renvoie un DataFrame comportant le detail du calendrier des paiements des indemnites.

        Parameters
        ----------
        - MoisPeriode : dict, 
            Un dictionnaire {Numero periode : Numero mois}.
        - DateMois :  str,
            Les dates de paiement des indemnités en focntion de la date d'admission théorique.
        - IndemniteBrut : float,
            Les montants des indemnités brutes.
        - IndemniteNet : float.
            Les montants des indemnités nettes.
        - PartPatronale : float.
            Les montants de la part patronale à la charge de la CNAC.
        
        Returns
        -------
        Un DataFrame.
        '''
        Periodes=[MoisPeriode[p] for p in MoisPeriode]
        Mois = [p for p in MoisPeriode]
        DateMois=[p for p in DateMois]
        IndemniteBrut=[p for p in IndemniteBrut]
        IndemniteNet = [p for p in IndemniteNet]
        PartSalariale = [Brut - Net for Brut, Net in zip(IndemniteBrut, IndemniteNet) ]
        PartPatronale=[p for p in PartPatronale]

        TableauRAC={"Periode":Periodes,
        "Mois":Mois,
        "Date":DateMois,
        "Montant Indemnité Brut":[p for p in IndemniteBrut],
        "Cotisation SS (PS)":[p for p in PartSalariale],
        "Montant Indemnité Net":[p for p in IndemniteNet],
        "Cotisation SS (PP)":[p for p in PartPatronale]}
        
        df = pd.DataFrame(TableauRAC)
        
        # {:,.2f}".format(p).replace(',', ' ').replace('.', ',') for p in IndemniteBrut
        return df   
    
    def Cal_DateFDD(self, DateMois):
        '''
        Calcul la date de fin de droits théorique en fonction du clendrier de paiements des indemnités.


        Parameters
        ----------
        DateMois : dict.
        Un dictionnaire {Numero periode : Numero mois}.
        
        Returns
        -------
        La date de fin de droits théorique.
        Elle représente le dernier mois de paiement de l'indemnité.
        '''
        if self.annee < 3 :
            DateFDD = datetime(1900,1,1)
        else:
            DateFDD = DateMois[-1]
        return DateFDD



class RAC_RRA(RAC):
    '''
    REGIME ASSURANCE CHOMAGE : SIMULATEUR

    Cette Class en python permet de réaliser des simulations pour le calculs des différents éléments liés au régime d'assurance chômage.
    Elle permet de :
    - Vérifier la condition d'admission relative à l'experience professionnelle;
    - Calculer la durée de prise en charge (DPC);
    - Calculer le montant de la Contribution d'Ouverture de Droits;
    - Récupérer le montant du SNMG en fonction de la date;
    - Calculer les montants d'indemnités en fonction des 04 périodes;
    - Calculer les montants de cotisations de sécurité sociale (part patronale & part salariale );

    Parameters
    ----------

    DateRecrutement : date, 
        C'est de la date de recrutement du salarié chez le dernier employeur.
        Elle doit être exprimé selon le format : dd/mm/yyyy.


    DateCompression : date,
        C'est la de compression du salarié chez le dernier employeur.
        Elle doit être exprimé selon le format : dd/mm/yyyy.

    
    SMM : float,
        C'est le Salaire Mensuel Moyen des 12 derniers mois.
        Il doit être exprimé en DA et concerne la moyenne des salaires soumis à cotisation de sécurité sociale des 12 derniers mois.

    genre : string,
        C'est le genre de l'allocataire.
        Il prend deux valeurs : Un Homme / Une Femme
    

    Attributes
    ----------

    annee : int,
        C'est la durée d'experience en année;

    mois : int,
        C'est la durée d'experience en mois lorsque la période est inferieure à une année;
    
    jours : int,
        C'est la durée d'experience en jours lorsque la période est inferieure à un mois;
    '''
    
    def __init__(self, DateRecrutement, DateCompression, SMM, DateNaissance, Genre):
        self.Datenaissance = DateNaissance
        self.Genre = Genre
        super().__init__(DateRecrutement, DateCompression, SMM)        
    
    def Cal_AgeDateRRA(self, DateFDD):
        '''
        Calcul l'age du salarié et la date a laquelle le salarié a épuisé ses droits à la CNAC.


        Parameters
        ----------
        DateFDD : str.
        La date de fin de droits théorique.
        
        Returns
        -------
        - age : l'age du salarié aprés epuisement de ses droits.
        - Adm_RRA : la date d'epuisement des droits du slarié.
        '''
        if self.annee < 3 :
            age = 0
            Adm_RRA = datetime.now()
        else :
            Adm_RRA = DateFDD + relativedelta.relativedelta(months=1)

            d1 = Adm_RRA
            d2 = datetime.strptime(self.Datenaissance, "%d/%m/%Y")
            
            delta = relativedelta.relativedelta(d1, d2)
            
            age = delta.years
        return  age, Adm_RRA
    
    def Verif_AdmissionRRA(self, age):
        '''
        Verifie les conditions d'admissions relatives au régime de la retraite anticipée aprés épuisement de droits du salarie.

        Parameters
        ----------
        age : int,
        Age du salarié aprés épuisement de ses droits.
        
        Returns
        -------
        AdmissionRRA : Une valeur string qui prend 03 possibilites : 
                    "Admis"--> Le salarié remplis les conditions de la retraite anticipée relative a son age et a son genre.
                    "Non Admis" --> Le salarié ne remplis pas les conditions de la retraite anticipée relative a son age et a son genre.
        '''
        if self.annee < 3 :
            AdmissionRRA=""
        if (self.Genre == "Un Homme" and age >= 50 and age < 60) or (self.Genre == "Une Femme" and age >= 45 and age < 55):
            AdmissionRRA="Admis"
        elif (age >= 60 and self.Genre == "Un Homme") or (age >= 55 and self.Genre == "Une Femme"):
            AdmissionRRA="Non Admis"
        return AdmissionRRA
        
    def Message_AdmissionRRA(self, age):
        '''
        Renvoie un message aprés verification des conditions d'admission au régime de la retraite anticipée aprés epuisement de droits du salarié.

        Parameters
        ----------
        age : int,
        Age du salarie aprés épuisement de ses droits.
        
        Returns
        -------
        MessageRRA : Un message selon le cas : "Admis" et "Non admis.
        '''
        if self.annee < 3 :
            MessageRRA=""
        if (self.Genre == "Un Homme" and age >= 50 and age < 60) or (self.Genre == "Une Femme" and age >= 45 and age < 55):
            MessageRRA="Selon votre age calculé, vous pouvez bénéficier du régime de la retraite anticipée aprés épuisement de vos droits au RAC à condition de remplir les autres conditions exigées par la CNR."
        elif (age >= 60 and self.Genre == "Un Homme"):
            MessageRRA = "Selon votre age calculé, vous aurez 60 ans ou plus aprés épuisement de vos droits, vous ne pouvez pas bénéficier du régime de la retraite anticipée"
        
        elif (age >= 55 and self.Genre == "Une Femme"):
            MessageRRA="Selon votre age calculé, vous aurez 55 ans ou plus aprés épuisement de vos droits, vous ne pouvez pas bénéficier du régime de la retraite anticipée"

        return MessageRRA
    
    
    def Cal_NombreAnneeAnt(self, age, AdmissionRRA):
        '''
        Calcul le nombre d'année d'ancticipation induit par la retraite ancticpée.

        Parameters
        ----------
        - age : int,
            Age du salarié aprés épuisement de ses droits.

        - AdmissionRRA : str.
            Un message selon le cas : "Admis" et "Non admis.       

        Returns
        -------
        Le nombre d'année de prise en charge par la CNR dans le cadre du régime de la retraite anticipée.
        '''
        if AdmissionRRA == "Non Admis":
            AnneeAnt = 0
        else:

            if self.Genre == "Un Homme":
                AnneeAnt = 60 - int(age)
            else:
                AnneeAnt = 55 - int(age)
        return AnneeAnt

    def Cal_CFOD(self, AdmissionRRA, AnneeAnt, CODTotale):
        '''
        Calcul le montant de la contribution forfetaire d'ouverture de droits CFOD.


        Parameters
        ----------

        - AdmissionRRA : str.
            Un message selon le cas : "Admis" et "Non admis.   
        - AnneeAnt : int,
            Le nombre d'année d'anticipation.
        - CODTotale :float,
            Le montant de la COD totale payé par l'employeur.


        Returns
        -------
        Le montant de la contribution forfetaire d'ouverture de droits CFOD.
        '''
        if AdmissionRRA == "Non Admis":
            CFOD = 0
        else:
            CFOD = (CODTotale * 0.3) + (AnneeAnt * 0.04 * CODTotale)
        return CFOD

    def Cal_CotisCNR(self, AnneeAnt, snmg):
        '''
        Renvoie un tableau du calendrier des paiements de la CFOD par la CNAC en fonction du nombre de d'année d'anticipation et le snmg.


        Parameters
        ----------
  
        - AnneeAnt : int,
            Le nombre d'année d'anticipation.
        - snmg :float,
            Le salaire national minimum garanti.


        Returns
        -------
        - AnneeCNR : Le nombre d'année de prise en charge par la CNR dans le cadre du régime de la retraite anticipée.
        - MoisCNR : Le nombre de mois par année de prise en charge par la CNR dans le cadre du régime de la retraite anticipée.
        - PartPatronaleCNR : Le montant de la cotisation de securité sociale a verser par la CNAC au profit des allocataires admis au regime 
          de la retraite anticpee  au niveau de la CNR.
        '''

        AnneeCNR =[]
        MoisCNR = []
        PartPatronaleCNR =[]
        for a in range(1, AnneeAnt+1):
            for b in range(1,13):
                MoisCNR.append(b)
                AnneeCNR.append(a)
                PartPatronaleCNR.append(round((0.14 * snmg),2))          
        return AnneeCNR, MoisCNR, PartPatronaleCNR





