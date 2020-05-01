#################### PROGRAMA PRA DIMENSIONAMENTO DE VIGA ####################

import numpy as np 
import csv as csv
from tkinter import *
from tkinter import ttk 
from tkinter.messagebox import *
from tkinter.filedialog import *

# CRIAÇÃO DO BANCO DE DADOS
classes_concreto = {'C20':20,'C25':25,'C30':30,'C35':35,'C40':40,'C45':45,
'C50':50,'C55':55,'C60':60,'C65':65,'C70':70,'C75':75,'C80':80,'C85':85,'C90':90}

categorias_aco = {'CA-25':250,'CA-50':500,'CA-60':600}

tipos_agregado = {'basalto e diabásio':1.2, 'granito e gnaisse':1.0, 'calcário':0.90, 'arenito':0.70}

taxa_min_As = {'C20':0.150,'C25':0.150,'C30':0.150,'C35':0.164,'C40':0.179,'C45':0.194,
'C50':0.208,'C55':0.210,'C60':0.219,'C65':0.226,'C70':0.233,'C75':0.239,'C80':0.245,'C85':0.251,'C90':0.256}

diametros = {'Ø5.0':5.0,'Ø6.3':6.3,'Ø8.0':8.0,'Ø10.0':10.0,'Ø12.5':12.5,'Ø16.0':16.0,'Ø20.0':20.0}

class PropConcretoArmado:
    # concreto 
    gamac = 1.4
    coef_dilat_conc = 0.00001
    # aço
    Es = 210000
    gamas = 1.15
    coef_dilat_aco = 0.00001
    es = 10/1000
    
    ### Propriedades definidas pelo usuário ###

    def __init__ (self, fck, fyk, alphae=1.0):
        """ Constrói os atributos de cada instância da classe (self),
        função do tipo de concreto e tipo de agregado"""
        self.fck = fck
        self.alphae = alphae
        self.fyk = fyk
        self.pmin = 0.01*taxa_min_As['C'+str(fck)]
        
        ### Propriedades calculadas a partir dos parâmetros inseridos ###
        
        if fck <= 50:
            self.alphac = 0.85
            self.lamb = 0.80
            self.xdlim = 0.45
            self.ec2 = 2/1000
            self.ecu = 3.5/1000
            self.n = 2 # coef. p/ diagrama tensão x deformação 
            self.fctm = 0.3*(fck)**(2/3)
            self.Eci = alphae*5600*(fck)**0.5
        else:
            self.alphac = 0.85*(1-(fck-50)/200)
            self.lamb = 0.8-(fck-50)/400
            self.xdlim = 0.35
            self.ec2 = 2/1000 + 0.000085*(fck-50)**0.53
            self.ecu = 2.6/1000 + 0.035*((90-fck)/100)**4
            self.n = 1.4 + 23.4*((90-fck)/100)**4 # coef. p/ diagrama tensão x deformação
            self.fctm = 2.12*np.log(1+0.11*fck)
            self.Eci = 21500*alphae*(0.1*fck+1.25)**(1/3)
        
        self.fyd = fyk/self.gamas
        self.fc = self.alphac*fck/self.gamac
        self.fctkinf = 0.7*self.fctm
        self.fctd = self.fctkinf/self.gamac
        self.fctksup = 1.3*self.fctm

        if fck > 80:
            self.alphai = 1
        else:
            self.alphai = 0.8 + 0.2*fck/80
       
        self.Ecs = self.alphai*self.Eci
        self.Gc = self.Ecs/2.4
        return

class FSSR(PropConcretoArmado): # Flexão Simples de Seção Retangular
    def calculo_As(self, d, dlinha, b, Md):
        self.d = d
        self.dlinha = dlinha
        self.b = b
        self.Md = Md

        ### POSIÇÃO DA LINHA NEUTRA ###
        self.y = d - (d**2-2*Md/(b*self.fc*0.1))**(0.5)
        self.y23 = (self.lamb)*self.ecu*d/(self.ecu+self.es)
        self.ydutil = (self.lamb)*self.xdlim*d 
        self.y34 = (self.lamb)*self.ecu*self.Es*0.1*d/(self.fyd*0.1+self.ecu*self.Es*0.1)
        self.ymax = min(self.ydutil, self.y34)
       
        ### CÁLCULO DA ARMADURA
        self.AsMin = self.pmin*b*d
        if 0 < self.y <= self.ymax: # Armadura Simples
            self.AsTracao = b*self.y*self.fc*0.1/(self.fyd*0.1)
            self.AsCompressao = 0
        elif self.y > self.ymax: # Armadura Dupla
            self.y = self.ymax
            self.Mdlim = self.b*self.y*self.fc*0.1*(d-0.50*self.y)
            self.e2 = self.ecu*(self.y-self.lamb*dlinha)/self.y
            if self.e2 > self.fyd/self.Es:
                self.sigma2 = self.fyd*0.1
            else:
                self.sigma2 = self.Es*0.1*self.e2
            self.AsCompressao = (Md-self.Mdlim)/(self.sigma2*(d-dlinha))
            self.AsTracao = (b*self.y*self.fc*0.1+self.AsCompressao*self.sigma2)/(self.fyd*0.1)
        self.xLN = self.y/self.lamb

        ### DOMÍNIIO DE DEFORMAÇÃO ###
        if self.y < self.y23:
            self.Dominio = 2
        elif self.y23 < self.y < self.y34:
            self.Dominio = 3
        return

 #################### INTERFACE GRÁFICA ###################

menu_inicial = Tk()
menu_inicial.title('ESTRUTURAS DE CONCRETO ARMADO')
menu_inicial.geometry('655x600')

###### CRIAÇÃO DOS COMANDOS ######

def dimensiona():
    tipo_concreto = str(comb_conc.get())
    tipo_aco = str(comb_aco.get())
    tipo_agregado = str(comb_agr.get())
    b_adot = float(entrada_b.get())
    d_adot = float(entrada_d.get())
    dlinha_adot = float(entrada_dlinha.get())
    Md_adot = float(entrada_Md.get())
    
    fck = int(classes_concreto[tipo_concreto])
    fyk = int(categorias_aco[tipo_aco])
    alphae = float(tipos_agregado[tipo_agregado])

    flexao_simples = FSSR(fck, fyk, alphae) # Cria o material
    flexao_simples.calculo_As(d_adot, dlinha_adot, b_adot, Md_adot) # Cria a Viga
    
    xLN.set(f"{flexao_simples.xLN:.2f}")
    Dominio.set(f"{flexao_simples.Dominio}")
    AsTracao.set(f"{flexao_simples.AsTracao:.2f}")
    AsCompressao.set(f"{flexao_simples.AsCompressao:.2f}")
    AsMin.set(f"{flexao_simples.AsMin:.2f}")
    a = float(AsTracao.get())
    b = float(AAdot.get())
    if b <= a:
        Label(menu_inicial,width=7,height=1,text="Não OK!",fg="red",font='Arial 9 bold').grid(row=7,padx=5,column=4,pady=2,sticky=W)
    else:
        Label(menu_inicial,width=7,height=1,text="OK!",fg="green",font='Arial 9 bold').grid(row=7,padx=5,column=4,pady=2,sticky=W)

def Sair():
    menu_inicial.destroy()

def Sobre():
    showinfo("CONCRETO ARMADO", """Criado por Eng. Marcos Wilson Ogata
    \nCREA: RS243165\nTodos os direitos reservados""")

def Area(event):
    Dados = [entrada_qtbarras1.get(), 
             entrada_qtbarras2.get(), 
             entrada_qtbarras3.get(), 
             comb_diametros1.get(),
             comb_diametros2.get(), 
             comb_diametros3.get()]

    for i in range(0,len(Dados)):
        if i < 3:
            try:
                Dados[i] = float(Dados[i])
            except ValueError:
                Dados[i] = 0
        else:
            try:
                diametro_barra = float(diametros[Dados[i]])
                Dados[i] = diametro_barra
            except:
                Dados[i] = 0
    AreaTotal = 0
    for i in range(0,3):
        AreaTotal += 0.25*Dados[i]*np.pi*(0.1*Dados[i+3])**2
    try:
        AAdot.set(f"{AreaTotal:.2f}")
        a = float(AsTracao.get())
        b = float(AAdot.get())
        if b <= a:
            Label(menu_inicial,width=7,height=1,text="Não OK!",fg="red",font='Arial 9 bold').grid(row=7,padx=5,column=4,pady=2,sticky=W)
        else:
            Label(menu_inicial,width=7,height=1,text="OK!",fg="green",font='Arial 9 bold').grid(row=7,padx=5,column=4,pady=2,sticky=W)
    except:
        pass

### DEFINIÇÃO DOS RÓTULOS, BOTÕES E CAIXAS DE COMBINAÇÃO ###

rotulo_titulo = Label(menu_inicial,text="DIMENSIONAMENTO DE VIGA DE CONCRETO ARMADO",justify="center",font='Arial 14 bold')
rotulo_titulo.grid(row=0,column=0,pady=10,columnspan=8)

rotulo_materiais = Label(menu_inicial,text="a) Definição dos Materiais:",font='Arial 10 bold')
rotulo_materiais.grid(row=1,column=0,pady=5,columnspan=4,sticky=W)

rotulo_conc = Label(menu_inicial,text="Classe do Concreto:")
rotulo_conc.grid(row=2,column=0,sticky=W)
comb_conc = ttk.Combobox(menu_inicial,width=7,justify="center",values=list(classes_concreto.keys()))
comb_conc.grid(row=2,column=1,pady=2,sticky=E)

rotulo_aco = Label(menu_inicial,justify="left",text="Categoria do aço:")
rotulo_aco.grid(row=2,padx=10,column=2,sticky=W)
comb_aco = ttk.Combobox(menu_inicial,width=7,justify="center",values=list(categorias_aco.keys()),state=DISABLED) # transforma as keys do dicionário em uma lista
comb_aco.grid(row=2,column=3,pady=2,sticky=E)
comb_aco.set("CA-50")

rotulo_agr = Label(menu_inicial,justify="left",text="Tipo\nde agregado:")
rotulo_agr.grid(row=2,padx=10,column=4,sticky=W)
comb_agr = ttk.Combobox(menu_inicial,width=16,justify="center",values=list(tipos_agregado.keys()))
comb_agr.grid(row=2,padx=10,column=5,pady=2,sticky=W)

rotulo_secao = Label(menu_inicial,text="b) Definição da Seção Transversal:", font='Arial 10 bold')
rotulo_secao.grid(row=3,column=0,pady=5,columnspan=2, sticky=W)

rotulo_b = Label(menu_inicial,text="Largura b (cm):")
rotulo_b.grid(row=4,column=0,sticky=W)
entrada_b = Entry(menu_inicial,width=10,borderwidth=1,justify="right")
entrada_b.grid(row=4,column=1,sticky=E)

rotulo_d = Label(menu_inicial,text="Altura útil d (cm):")
rotulo_d.grid(row=5,column=0,sticky=W)
entrada_d = Entry(menu_inicial,width=10,borderwidth=1,justify="right")
entrada_d.grid(row=5,column=1,sticky=E)

rotulo_dlinha = Label(menu_inicial,text="Altura útil d' (cm):")
rotulo_dlinha.grid(row=6,column=0,sticky=W)
entrada_dlinha = Entry(menu_inicial,width=10,borderwidth=1,justify="right")
entrada_dlinha.grid(row=6,column=1,sticky=E)

rotulo_Md = Label(menu_inicial,text="Momento MSd (kNcm):",justify="left")
rotulo_Md.grid(row=7,column=0,sticky=W)
entrada_Md = Entry(menu_inicial,width=10,borderwidth=1,justify="right")
entrada_Md.grid(row=7,column=1,sticky=E)

botao_calcular = Button(menu_inicial,text="Calcular Armadura!",width=25,command=dimensiona)
botao_calcular.grid(row=8,column=0,columnspan=2,pady=2)

rotulo_resultado = Label(menu_inicial,text="c) Resultados do Cálculo", font='Arial 10 bold',fg='red')
rotulo_resultado.grid(row=9,column=0,pady=5,columnspan=2,sticky=W)

xLN = Variable()
Dominio = Variable()
AsTracao = Variable()
AsCompressao = Variable()
AsMin = Variable()
AAdot = Variable()

Label(menu_inicial,text="Posição da Linha Neutra X (cm):",justify="left").grid(row=10,column=0,sticky=W)
rotulo_x = Label(menu_inicial,textvariable=xLN,width=8,height=1,justify="right",bg="gainsboro")
rotulo_x.grid(row=10,column=1,pady=2,sticky=E)

Label(menu_inicial,text="Domínio de Deformação:").grid(row=11,column=0,sticky=W)
rotulo_Dominio = Label(menu_inicial,textvariable=Dominio,width=8,height=1,justify="right",bg="gainsboro")
rotulo_Dominio.grid(row=11,column=1,pady=2,sticky=E)

Label(menu_inicial,text="Armadura de Tração (cm²):").grid(row=12,column=0,sticky=W)
rotulo_AsTracao = Label(menu_inicial,textvariable=AsTracao,width=8,height=1,justify="right",bg="gainsboro")
rotulo_AsTracao.grid(row=12,column=1,pady=2,sticky=E)

Label(menu_inicial,text="Armadura de Compressão (cm²):").grid(row=13,column=0,sticky=W)
rotulo_AsCompressao = Label(menu_inicial,textvariable=AsCompressao,width=8,height=1,justify="right",bg="gainsboro")
rotulo_AsCompressao.grid(row=13,column=1,pady=2,sticky=E)

Label(menu_inicial,text="Armadura Mínima (cm²):").grid(row=14,column=0,sticky=W)
rotulo_AsMin = Label(menu_inicial,textvariable=AsMin,width=8,height=1,justify="right",bg="gainsboro")
rotulo_AsMin.grid(row=14,column=1,pady=2,sticky=E)

Label(menu_inicial,text="Armadura de Tração",font='Arial 10 bold').grid(row=3,padx=10,column=2,columnspan=2,sticky=W)

Label(menu_inicial,text="1ª camada:").grid(row=4,padx=10,column=2,sticky=W)
entrada_qtbarras1 = Entry(menu_inicial,width=10,borderwidth=1,justify="right")
entrada_qtbarras1.bind("<KeyRelease>",Area)
entrada_qtbarras1.insert(END,"0")
entrada_qtbarras1.grid(row=4,column=3,pady=2,sticky=E)
comb_diametros1 = ttk.Combobox(menu_inicial,width=5,justify="center",values=list(diametros.keys()))
comb_diametros1.bind("<<ComboboxSelected>>",Area)
comb_diametros1.grid(row=4,padx=5,column=4,pady=2,sticky=W)

Label(menu_inicial,text="2ª camada:").grid(row=5,padx=10,column=2,sticky=W)
entrada_qtbarras2 = Entry(menu_inicial,width=10,borderwidth=1,justify="right")
entrada_qtbarras2.bind("<KeyRelease>",Area)
entrada_qtbarras2.insert(END,"0")
entrada_qtbarras2.grid(row=5,column=3,pady=2,sticky=E)
comb_diametros2 = ttk.Combobox(menu_inicial,width=5,justify="center",values=list(diametros.keys()))
comb_diametros2.bind("<<ComboboxSelected>>",Area)
comb_diametros2.grid(row=5,padx=5,column=4,pady=2,sticky=W)

Label(menu_inicial,text="3ª camada:").grid(row=6,padx=10,column=2,sticky=W)
entrada_qtbarras3 = Entry(menu_inicial,width=10,borderwidth=1,justify="right")
entrada_qtbarras3.bind("<KeyRelease>",Area)
entrada_qtbarras3.insert(END,"0")
entrada_qtbarras3.grid(row=6,column=3,pady=2,sticky=E)
comb_diametros3 = ttk.Combobox(menu_inicial,width=5,justify="center",values=list(diametros.keys()))
comb_diametros3.bind("<<ComboboxSelected>>",Area)
comb_diametros3.grid(row=6,padx=5,column=4,pady=2,sticky=W)

Label(menu_inicial,text="Área Total (cm²):").grid(row=7,padx=10,column=2,sticky=W)
Label(menu_inicial,width=8,height=1,textvariable=AAdot,bg="gainsboro").grid(row=7,column=3,pady=2)

###### CRIAÇÃO DO MENU SUPERIOR ######



menu_inicial.mainloop()
