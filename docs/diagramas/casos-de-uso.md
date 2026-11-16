# Diagrama de Casos de Uso

usecaseDiagram
    actor "Agente Cliente (AC)" as AC
    actor "Agente Atendente (AA)" as AA
    actor "Gestor" as G
    
    package LabManager {
        usecase "Emitir Senha (Totem)" as UC1
        usecase "Acompanhar Painel" as UC2
        usecase "Chamar Próxima Senha" as UC3
        usecase "Chamar Novamente" as UC4
        usecase "Iniciar/Encerrar Atendimento" as UC5
        usecase "Extrair Relatórios" as UC6
        usecase "Gerenciar Usuários" as UC7
    }
    
    AC --> UC1
    AC --> UC2
    
    AA --> UC3
    AA --> UC4
    AA --> UC5
    
    G --> UC6
    G --> UC7