#!/usr/bin/env python3

import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse

def scan_port(host, port, timeout=2):
    """
    Tenta conectar em uma porta específica através do proxychains
    """
    try:
        # Usa proxychains4 com nc para testar a porta
        cmd = ['proxychains4', '-q', 'nc', '-zv', '-w', str(timeout), host, str(port)]
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout + 1,
            text=True
        )
        
        # nc retorna 0 se a conexão foi bem-sucedida
        if result.returncode == 0 or 'succeeded' in result.stderr.lower():
            return port, True
        return port, False
    except subprocess.TimeoutExpired:
        return port, False
    except Exception as e:
        return port, False

def scan_ports(host, start_port=1, end_port=65535, threads=50, timeout=2):
    """
    Escaneia um range de portas
    """
    print(f"[*] Iniciando scan em {host}")
    print(f"[*] Range de portas: {start_port}-{end_port}")
    print(f"[*] Threads: {threads}")
    print(f"[*] Timeout: {timeout}s\n")
    
    open_ports = []
    
    with ThreadPoolExecutor(max_workers=threads) as executor:
        # Submete todas as tarefas
        futures = {
            executor.submit(scan_port, host, port, timeout): port 
            for port in range(start_port, end_port + 1)
        }
        
        # Processa resultados conforme completam
        completed = 0
        total = len(futures)
        
        for future in as_completed(futures):
            port, is_open = future.result()
            completed += 1
            
            if is_open:
                print(f"[+] Porta {port}/tcp está ABERTA")
                open_ports.append(port)
            
            # Mostra progresso a cada 100 portas
            if completed % 100 == 0:
                print(f"[*] Progresso: {completed}/{total} portas testadas")
    
    return open_ports

def main():
    parser = argparse.ArgumentParser(
        description='Port Scanner usando proxychains4',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Exemplos:
  %(prog)s 10.10.150.10                    # Scan completo (portas 1-65535)
  %(prog)s 10.10.150.10 -p 1-1000          # Scan portas 1-1000
  %(prog)s 10.10.150.10 -p 80,443,8080     # Scan portas específicas
  %(prog)s 10.10.150.10 -t 100 --timeout 3 # 100 threads, timeout 3s
        '''
    )
    
    parser.add_argument('host', help='Host alvo (ex: 10.10.150.10)')
    parser.add_argument('-p', '--ports', default='1-65535',
                       help='Range de portas (ex: 1-1000 ou 80,443,8080)')
    parser.add_argument('-t', '--threads', type=int, default=50,
                       help='Número de threads (padrão: 50)')
    parser.add_argument('--timeout', type=int, default=2,
                       help='Timeout por porta em segundos (padrão: 2)')
    
    args = parser.parse_args()
    
    # Processa range de portas
    if ',' in args.ports:
        # Portas específicas
        ports = [int(p.strip()) for p in args.ports.split(',')]
        start_port = min(ports)
        end_port = max(ports)
    elif '-' in args.ports:
        # Range de portas
        start_port, end_port = map(int, args.ports.split('-'))
    else:
        # Porta única
        start_port = end_port = int(args.ports)
    
    try:
        open_ports = scan_ports(
            args.host,
            start_port,
            end_port,
            args.threads,
            args.timeout
        )
        
        print("\n" + "="*50)
        print(f"[*] Scan completo!")
        print(f"[*] Total de portas abertas: {len(open_ports)}")
        
        if open_ports:
            print("\n[+] Portas abertas encontradas:")
            for port in sorted(open_ports):
                print(f"    - {port}/tcp")
        else:
            print("\n[-] Nenhuma porta aberta encontrada")
        
    except KeyboardInterrupt:
        print("\n\n[!] Scan interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n[!] Erro: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
