import py_dss_interface
import os
import pathlib
import random
import pandas as pd

# Define o caminho do arquivo do opendss para ser usado como base para o código
script_path = os.path.dirname(os.path.abspath(__file__))
dss_file = pathlib.Path(script_path).joinpath("../feeders", "37BUS", "ieee37.dss")

# Define o objeto dss, usado para chamar as funções da biblioteca
dss = py_dss_interface.DSS()

# Parâmetros da simulação: 
paineis_ativados = True     # Para conectar os painéis à simulação paineis_ativados = true, para retirar paineis_ativados = false
storage = False    # Para ativar o controle do inversor volt_var_ativado=true, para desativar volt_var_ativado=false

casename = "DI"
dss.text(f"compile [{dss_file}]")

dss.text("Set casename={}".format(casename))

dss.text("Set mode = daily")    # Define o modo de simulação diária
dss.text("Set stepsize = 1h") # Definie o passo da simulação
dss.text("Set number = 24") # Número de passos a serem simulados

# Configuração do Demand Interval (DI)
dss.text("Set demandinterval=true DIVerbose=true")
dss.text("Set overloadreport=true voltexcept=true")
dss.text("Set normvminpu=0.93 normvmaxpu=1.05") # Definição dos parâmetros de transgressão de tensão

# Loadshape diário com 24 pontos com característica residencial
dss.text("New LoadShape.residencial npts=24 interval=1 "
         "mult=(.25 .20 .18 .18 .18 .24 .41 .61 .63 .63 .67 .60 .72 .65 .56 .49 .46 .64 .80 .91 .81 .60 .56 .38 .38)")

# Loadshape diário com 24 com característica comercial
dss.text("New LoadShape.comercial npts=24 interval=1 "
         "mult=(.33 .32 .28 .3 .37 .47 .68 .87 .98 .98 .98 .79 .82 .85 .85 .85 .79 .55 .49 .45 .41 .39 .35 .34)")

# Define o loadshape de todas as cargas para comportamento residencial
dss.text("BatchEdit Load..* daily=residencial")

# Aumento da potência nominal do transformar em 1000 kVA para suportar as cargas residenciais
dss.text("BatchEdit Transformer.SubXF wdg=1 kva=3500")
dss.text("BatchEdit Transformer.SubXF wdg=2 kva=3500")

all_bus_names = dss.circuit.buses_names
all_bus_names.remove('sourcebus') # Remove a barra de referência da seleção

percent = 0.8  # Percentual de barras com GD
random.seed(3) # Padroniza a seleção aleatória
selected_buses = random.sample(all_bus_names, int(percent * len(all_bus_names))) # Seleciona um conjunto aleatório de barras para alocar as GDs

# Características dos painéis
kv = 4.8     # Tensão de linha [kV]
kva = 100     # Potência nominal do inversor [kVA]
pmpp = 100    # Ponto de máxima potência [kVA]
fp = 1       # Fator de potência

# Características das baterias
kwh = 500   # Capacidade da bateria
kw = 75     # Potência da bateria

dss.text("New XYCurve.MyPvsT npts=4  xarray=[0  25  75  100]  yarray=[1.2 1 0.8 0.6]") # Curva representado a relação entre capacidade de geração e temperatura
dss.text("New XYCurve.MyEff npts=4  xarray=[.1  .2  .4  1.0]  yarray=[.86 .9 .93 .97]") # Curva representando a eficiência do painel

dss.text("New loadshape.Irrad npts=24 interval=1 "
         "mult=[0 0 0 0 0 0 .1 .2 .3 .5 .8 .9 1.0 1.0 .99 .9 .7 .4 .1 0 0 0 0 0]") # Curva diária de irradiância

dss.text("New Tshape.Temp npts=24  interval=1 "
         "temp=[25 25 25 25 25 25 25 25 35 40 45 50 60 60 55 40 35 30 25 25 25 25 25 25]") # Curva diária de temperatura

# Alocação dos painéis nas barras selecionadas
for bus in selected_buses:
    dss.text(f"New PVSystem.PV_{bus} phases=3 conn=delta bus1={bus} kV={kv} kVA={kva} Pmpp={pmpp} pf={fp}"
             f" Daily=Irrad Tdaily=Temp Temperature=25 Irradiance=0.98 %cutin=0.1 %cutout=0.1"
             f" effcurve=Myeff  P-TCurve=MyPvsT vmaxpu=2 vminpu=0.5 debugtrace=false enabled={paineis_ativados}") # Parametrização dos PVs. Conexão em delta devido ao secundário do transformador da subestação, o qual não fornce o neutro.
    
    dss.text(f"New Storage.Stg{bus} kwrated={kw} kwhrated={kwh} kv={kv} phases=3 conn=delta "
             f"bus1={bus} state=idling %stored=20 %reserve=20") # Parametrização das baterias a serem alocadas em conjunto com os painéis
    
dss.text(f"New storagecontroller.stg_ctrl modecharge=time modedischarge=time "
         f"TimeChargeTrigger=10 TimeDischargeTrigger=20 element=transformer.subxf "
         f"enabled={storage}") # Definição do controle das baterias, sendo o início do carregamento definido para 10 hr e do descarregamento às 18 hr

# Definição dos monitores para vizualizar perfis de tensão e potência
dss.text("New monitor.Nivel_de_tensao_na_SE element=Line.L35 terminal=1 mode=0") # Monitora a barra 799, na cabeça do alimentador
dss.text("New monitor.Fluxo_de_potencia_na_SE element=transformer.subXF terminal=2 mode=1 ppolar=false") # Fluxo de potência na SE principal

dss.solution.solve() # Comando para realizar a simulação
dss.text("closedi") # Encerra o relatório DI

# Plot dos monitores
dss.text("Plot monitor object=Nivel_de_tensao_na_SE channels=(1 3 5) bases=[2771 2771 2771]") # Tensão monofásica em pu
dss.text("Plot monitor object=Fluxo_de_potencia_na_SE channels=(1 3 5)") # Potência ativa
dss.text("Plot monitor object=Fluxo_de_potencia_na_SE channels=(2 4 6)") # Potência reativa

# Rotina responsável por analisar o DI e trazer informações resumidas a respeito de sobretensões
folder = pathlib.Path(script_path).joinpath("../feeders", "37Bus", "DI", "DI_yr_0", "DI_VoltExceptions_1.CSV")

df = pd.read_csv(folder)

flag_overvoltage = False
for indice, linha in df.iterrows():
    if linha[' "Overvoltage"'] > 0:
        if flag_overvoltage == False:
            flag_overvoltage = True
            print("HOUVE SOBRETENSÃO")
        print("Hora: {}     Quantidade de barras com sobretensão: {}    Barra com maior tensão: {}      Maior nível de tensão: {}"
              .format(linha["Hour"], linha[' "Overvoltage"'], linha[' "Max Bus"'], linha[' "Max Voltage"']))

if flag_overvoltage == False:
    print("NÃO HOUVE SOBRETENSÃO")
    

# Rotina responsável por analisar o DI e trazer informações resumidas a respeito das sobrecargas
print(" ")
folder = pathlib.Path(script_path).joinpath("../feeders", "37Bus", "DI", "DI_yr_0", "DI_Overloads_1.CSV")

df = pd.read_csv(folder)

flag_overload = False
for indice, linha in df.iterrows():
    if linha["Hour"] > 0:
        if flag_overload == False:
            flag_overload = True
            print("HOUVE SOBRECARGA")
        print("Hora: {}     Elemento: {}    Porcentagem de sobrecarga: {}"
              .format(linha["Hour"], linha[' "Element"'], linha[' "% Normal"']))

if flag_overload == False:
    print("NÃO HOUVE SOBRECARGA")

print(" ")
