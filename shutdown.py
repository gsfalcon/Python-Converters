import os
import time

def agendar_desligamento(tempo_segundos, mensagem):
    print(f"\nSeu computador será desligado em {mensagem}.")
    print("Deseja continuar? (s/n)")
    resposta = input().lower()
    if resposta == 's':
        os.system(f'shutdown -a')  # Cancela qualquer agendamento anterior
        os.system(f'shutdown -s -t {tempo_segundos} -c "{mensagem}"')
        print("\nDesligamento programado com sucesso!")
    else:
        print("\nDesligamento cancelado.")

def cancelar_desligamento():
    os.system('shutdown -a')
    print("\nTodos os agendamentos foram cancelados.")

def main():
    while True:
        print("""
            S H U T D O W N - DESLIGAMENTO AUTOMÁTICO

            1 - Agendar para desligar em 15 minutos
            2 - Agendar para desligar em 30 minutos
            3 - Agendar para desligar em 45 minutos
            4 - Agendar para desligar em 1 hora
            5 - Agendar para desligar em 1 hora e meia
            6 - Agendar para desligar em 2 horas
            7 - Agendar para desligar em 10 horas
            8 - Cancelar todos os agendamentos
            9 - Sair
        """)
        
        opcao = input("Digite a opção desejada: ")
        
        if opcao == '1':
            agendar_desligamento(900, "15 minutos")
        elif opcao == '2':
            agendar_desligamento(1800, "30 minutos")
        elif opcao == '3':
            agendar_desligamento(2700, "45 minutos")
        elif opcao == '4':
            agendar_desligamento(3600, "1 hora")
        elif opcao == '5':
            agendar_desligamento(5400, "1 hora e meia")
        elif opcao == '6':
            agendar_desligamento(7200, "2 horas")
        elif opcao == '7':
            agendar_desligamento(36000, "10 horas (modo de descanso)")
        elif opcao == '8':
            cancelar_desligamento()
        elif opcao == '9':
            print("\nSaindo...")
            break
        else:
            print("\nOpção inválida. Tente novamente.")
        time.sleep(1)

if __name__ == "__main__":
    main()
