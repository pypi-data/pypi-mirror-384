
# Importer les modules

from cnaclib.tools import Region

##########################################################################################################################################
#                                                       MESURE D'ENCOURAGEMENT A L'EMPLOI (LOI 06-21) : SIMULATEUR
##########################################################################################################################################



class Recrutement():
    '''
    MESURE D'ENCOURAGEMENT A L'EMPLOI (LOI 06-21) : SIMULATEUR

    Cette  Classe en python permet de réaliser des simulations pour le calcul des  avantages liés à l’abattement sur cotisation sociale et à la subvention mensuelle à l’emploi.
        
    La classe 'Recrutement' permet de :
        - Calculer le taux d’abattement à la charge de la CNAC ;
        - Calculer le taux d’abattement à la charge du trésor ;
        - Calculer le montant de l’abattement à la charge de la CNAC ;
        - Calculer le montant de l’abattement à la charge du trésor ;
        - Calculer le montant de la cotisation de sécurité sociale à la charge de l’employeur avant abattement ;
        - Calculer le montant de la cotisation de sécurité sociale à la charge de l’employeur après abattement ;
        - Calculer le montant de la subvention mensuel à l’emploi à la charge de la CNAC ;
    
    Parameters
    ----------
    Wilaya : string default 'ADRAR', 
        C’est la wilaya du recrutement. Ce paramètre sert à trouver la région du recrutement. 
    
    primo_demandeur : boolean default False, 
        Spécifie si la personne recrutée est un primo-demandeur ou non. Ce paramètre prend deux valeur true or false.
    
    Contrat : int default 0, 
        Désigne le type du contrat de travail CDD ou CDI. Il prend deux valeur, 0 si CDD et 1 sinon.
    
    Salaire : float default 20000.0,
        C’est le salaire (moyen) soumis à cotisation de sécurité sociale du salarié recruté.

    
    Attributes
    ----------

    taux_CNAC : float,
        C'est le taux d'abattement à la charge de la CNAC,

    taux_tresor : floar,
        C'est le taux d'abattement à la charge du trésor,

    montant_quote_part_patronale : float,
        C'est le montant la cotisation de sécurité sociale à la charge de l'employeur sans abattement.
    
    montnat_Abattement_CNAC : float,
        C'est le montant la cotisation de sécurité sociale à la charge de la CNAC.
    
    montnat_Abattement_tresor : float, 
        C'est le montant la cotisation de sécurité sociale à la charge du trésor. 
    
    montant_Quote_part_a_paye_avec_CNAC : float,
        C'est le montant la cotisation de sécurité sociale à la charge de l'employeur avec abattement CNAC.
    
    montant_Quote_part_a_paye_avec_cnac_tresor : float,
        C'est le montant la cotisation de sécurité sociale à la charge de l'employeur avec abattement CNAC & abattement trésor.

    Montant_Sub : float,
        C'est le montant total de la subvention mensuelle à l'emploi à la charge de la CNAC.
'''    
    
    def __init__(self, Wilaya='ADRAR', primo_demandeur=False, Contrat=0, Salaire=20000.0):
        self.Wilaya = Wilaya
        self.primo = primo_demandeur
        self.contrat = Contrat
        self.Salaire = Salaire

    def Taux_Abattement(self):
        if Region(self.Wilaya, langue=0) == 'Nord':
            if self.primo:
                self.taux_CNAC = 0.28
                self.taux_tresor = 0.52
            else :
                self.taux_CNAC = 0.2
                self.taux_tresor = 0.2
        elif Region(self.Wilaya, langue=0) == 'Haut-Plateaux' or Region(self.Wilaya, langue=0) == 'Sud':
                self.taux_CNAC = 0.36
                self.taux_tresor = 0.54
        return self.taux_CNAC, self.taux_tresor

    
    def Montant_Abattement(self):
        self.montant_quote_part_patronale = self.Salaire * 0.25
        self.montnat_Abattement_CNAC = self.Taux_Abattement()[0] * self.montant_quote_part_patronale
        self.montnat_Abattement_tresor = self.Taux_Abattement()[1] * self.montant_quote_part_patronale
        self.montant_Quote_part_a_paye_avec_CNAC = self.montant_quote_part_patronale - self.montnat_Abattement_CNAC
        self.montant_Quote_part_a_paye_avec_cnac_tresor = self.montant_quote_part_patronale - self.montnat_Abattement_CNAC - self.montnat_Abattement_tresor
        return self.montant_quote_part_patronale, self.montnat_Abattement_CNAC, self.montnat_Abattement_tresor, self.montant_Quote_part_a_paye_avec_CNAC, self.montant_Quote_part_a_paye_avec_cnac_tresor

    def Montant_Subvention(self):
        if self.contrat == 0:
            self.Montant_Sub = 0.0
        else :
            self.Montant_Sub = 1000.0 * 36
        return self.Montant_Sub


class Formation():
    '''
    MESURE D'ENCOURAGEMENT A L'EMPLOI (LOI 06-21) : SIMULATEUR

    Cette  Classe en python permet de réaliser des simulations pour le calcul des  avantages liés à l'exonération mensuelle de la quote-part de sécurité sociale.
    
    La classe 'Formation' permet de :

        - Calculer le nombre de mois d'exonération de la quote-part patronale;
        - Calculer le montant de la cotisation mensuelle de sécurité sociale à la charge de l’employeur avant exonération ;
        - Calculer le montant de l'exonération mensuelle à la charge de la CNAC;
        - Calculer le montant de l'exonération totale pour toute la duré d'exonération à la charge de la CNAC;
    
    
    Parameters
    ----------
    duree_formation : int default 0, 
        C’est la durée de formation du salarié. Ce paramètre peut prendre 03 arguments : 0 --> la durée de formation >= 15 jrs et <= 01 mois,
        1 -- > la durée de formation > 01 mois et <= 02 mois, 3 --> la durée de formation > 02 mois.
       
    Salaire : float default 20000.0,
        C’est le salaire (moyen) soumis à cotisation de sécurité sociale du salarié en formation.

    
    Attributes
    ----------

    nbre_mois : int,
        C'est la durée d'exonération de la quote-part patronale en nombre de mois.
        Cet attribut prend 03 valeurs : 1 mois, 2 mois ou 3 mois.

    montant_quote_part_patronale : float, 
        C'est le montant la cotisation de sécurité sociale à la charge de l'employeur sans exonération.

    montant_mensuel_exoneration : float, 
        C'est le montant de l'exonération mensuelle à la charge de la CNAC.

    montant_total_exoneration: float, 
        C'est le montant de l'exonération totale pour toute la duré d'exonération à la charge de la CNAC.


    '''    
    
    def __init__(self, duree_formation=0, Salaire=20000.0):
        self.duree = duree_formation
        self.Salaire = Salaire
    
    
    def Nbre_Mois(self):
        if self.duree == 0 :
            self.nbre_mois = 1
        elif self.duree == 1:
            self.nbre_mois = 2
        else:
            self.nbre_mois = 3
        return self.nbre_mois
    
    def Montant_Formation(self):
        self.montant_quote_part_patronale = self.Salaire * 0.25
        self.montant_mensuel_exoneration = 1 * self.montant_quote_part_patronale
        self.montant_total_exoneration = self.nbre_mois * self.montant_mensuel_exoneration

        return self.montant_quote_part_patronale, self.montant_mensuel_exoneration, self.montant_total_exoneration




'''
if __name__=='__main__':
    nadir = Recrutement(Wilaya='ADRAR', primo_demandeur=False, Contrat=0,Salaire=50000)
    print(nadir.Taux_Abattement())
    print(nadir.Montant_Abattement())

    khaled = Formation(duree_formation=1, Salaire=25000)
    print(khaled.Nbre_Mois())
    print(khaled.Montant_Formation())
'''