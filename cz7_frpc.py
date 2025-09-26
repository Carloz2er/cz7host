#!/usr/bin/env python3
"""
CZ7 Host - FRPC Client Python
Cliente FRPC completo em Python puro para tunelamento
"""

import socket
import threading
import time
import json
import os
import sys
import random
import struct

class CZ7FRPC:
    def __init__(self):
        self.running = False
        self.config_file = "cz7_frpc_config.json"
        self.config = {}
        self.connection_id = 0
        self.connections = {}
        
    def display_banner(self):
        """Exibe banner da CZ7 Host"""
        banner = """
╔══════════════════════════════════════════════╗
║            CZ7 Host - FRPC Client            ║
║           Tunnel Client Professional         ║
║                                              ║
║    Conecte aplicações locais à internet     ║
║           de forma simples e rápida          ║
╚══════════════════════════════════════════════╝
        """
        print(banner)
    
    def parse_server_url(self, url):
        """Analisa a URL do servidor: br-01.cz7.host:30000"""
        try:
            if ":" in url:
                server_addr, server_port = url.split(":", 1)
                server_port = int(server_port)
            else:
                server_addr = url
                server_port = 7000  # default
            
            return server_addr, server_port
        except:
            return None, None
    
    def get_user_config(self):
        """Obtém configurações do usuário"""
        print("🔧 Configuração do Tunnel CZ7 Host")
        print("=" * 50)
        
        # URL completa do servidor (com porta)
        print("\n🌐 Configuração do Servidor FRPS:")
        print("💡 Cole a URL COMPLETA que você recebeu no Pterodactyl")
        print("   Exemplo: br-01.cz7.host:30000")
        
        server_url = input("URL do servidor: ").strip()
        if not server_url:
            print("❌ URL do servidor é obrigatória!")
            return False
        
        server_addr, server_port = self.parse_server_url(server_url)
        if not server_addr:
            print("❌ URL inválida! Use formato: dominio.com:porta")
            return False
        
        print(f"✅ Servidor: {server_addr}:{server_port}")
        
        # Token de autenticação
        token = input("Token de autenticação (do painel): ").strip()
        if not token:
            print("❌ Token é obrigatório!")
            return False
        
        # Configuração local
        print("\n💻 Configuração da Aplicação Local:")
        local_ip = input("IP local da aplicação [127.0.0.1]: ").strip() or "127.0.0.1"
        
        local_port = input("Porta LOCAL da aplicação (ex: 80, 3000, 8080): ").strip()
        if not local_port.isdigit():
            print("❌ Porta local deve ser um número!")
            return False
        local_port = int(local_port)
        
        # Nome do tunnel
        tunnel_name = input("Nome do tunnel [web_tunnel]: ").strip() or "web_tunnel"
        
        # Salvar configuração
        self.config = {
            "server_addr": server_addr,
            "server_port": server_port,
            "token": token,
            "local_ip": local_ip,
            "local_port": local_port,
            "tunnel_name": tunnel_name,
            "protocol": "tcp"
        }
        
        return self.save_config()
    
    def load_config(self):
        """Carrega configuração existente"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                print("✅ Configuração carregada do arquivo existente")
                
                # Mostrar resumo da configuração
                print("\n📋 Configuração atual:")
                print(f"   Servidor: {self.config['server_addr']}:{self.config['server_port']}")
                print(f"   Local: {self.config['local_ip']}:{self.config['local_port']}")
                print(f"   Tunnel: {self.config['tunnel_name']}")
                
                usar_existente = input("\nUsar esta configuração? (s/n) [s]: ").strip().lower()
                if usar_existente in ['', 's', 'sim']:
                    return True
            except Exception as e:
                print(f"❌ Erro ao carregar configuração: {e}")
        
        # Se não existe ou usuário quer nova config
        return self.get_user_config()
    
    def save_config(self):
        """Salva configuração no arquivo"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            print(f"✅ Configuração salva em: {self.config_file}")
            return True
        except Exception as e:
            print(f"❌ Erro ao salvar configuração: {e}")
            return False
    
    def send_msg(self, sock, msg_type, data=b''):
        """Envia mensagem formatada para o servidor"""
        try:
            # Formato: [tipo(1 byte)][comprimento(4 bytes)][dados]
            msg = struct.pack('!BI', msg_type, len(data)) + data
            sock.sendall(msg)
            return True
        except Exception as e:
            print(f"❌ Erro ao enviar mensagem: {e}")
            return False
    
    def recv_msg(self, sock):
        """Recebe mensagem formatada do servidor"""
        try:
            # Ler cabeçalho (5 bytes)
            header = sock.recv(5)
            if len(header) < 5:
                return None, None
            
            msg_type, length = struct.unpack('!BI', header)
            
            # Ler dados
            data = b''
            while len(data) < length:
                chunk = sock.recv(length - len(data))
                if not chunk:
                    return None, None
                data += chunk
            
            return msg_type, data
        except Exception as e:
            print(f"❌ Erro ao receber mensagem: {e}")
            return None, None
    
    def authenticate(self, sock):
        """Autentica com o servidor FRPS"""
        auth_data = {
            'version': '0.1',
            'hostname': socket.gethostname(),
            'user': 'cz7_client',
            'privilege_key': self.config['token'],
            'timestamp': time.time(),
            'run_id': random.randint(1000, 9999)
        }
        
        # Enviar autenticação
        if not self.send_msg(sock, 1, json.dumps(auth_data).encode()):
            return False
        
        # Aguardar resposta
        msg_type, data = self.recv_msg(sock)
        if msg_type == 2:  # Auth OK
            print("✅ Autenticação bem-sucedida")
            return True
        else:
            print("❌ Falha na autenticação")
            return False
    
    def create_proxy(self, sock):
        """Cria proxy no servidor"""
        proxy_data = {
            'proxy_name': self.config['tunnel_name'],
            'proxy_type': 'tcp',
            'use_encryption': True,
            'use_compression': True
        }
        
        if not self.send_msg(sock, 3, json.dumps(proxy_data).encode()):
            return False
        
        msg_type, data = self.recv_msg(sock)
        if msg_type == 4:  # Proxy created
            print(f"✅ Proxy criado: {self.config['tunnel_name']}")
            return True
        else:
            print("❌ Falha ao criar proxy")
            return False
    
    def handle_connection(self, client_sock, server_sock, conn_id):
        """Gerencia conexão individual"""
        def forward_data(source, dest, direction):
            try:
                while self.running:
                    data = source.recv(4096)
                    if not data:
                        break
                    dest.sendall(data)
            except:
                pass
            finally:
                try:
                    source.close()
                except:
                    pass
        
        # Threads para forwarding bidirecional
        t1 = threading.Thread(target=forward_data, args=(client_sock, server_sock, "→"))
        t2 = threading.Thread(target=forward_data, args=(server_sock, client_sock, "←"))
        
        t1.daemon = True
        t2.daemon = True
        
        t1.start()
        t2.start()
        
        t1.join()
        t2.join()
        
        # Remover da lista de conexões
        if conn_id in self.connections:
            del self.connections[conn_id]
        print(f"🔌 Conexão #{conn_id} finalizada")
    
    def start_tunnel(self):
        """Inicia o tunelamento principal"""
        print("\n🚀 Iniciando Tunnel CZ7 Host...")
        print(f"📡 Local: {self.config['local_ip']}:{self.config['local_port']}")
        print(f"🌐 Remoto: {self.config['server_addr']}:{self.config['server_port']}")
        print(f"🔗 Tunnel: {self.config['tunnel_name']}")
        print("=" * 50)
        
        self.running = True
        
        while self.running:
            try:
                # Conectar ao servidor FRPS
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(30)
                
                print(f"🔌 Conectando ao {self.config['server_addr']}:{self.config['server_port']}...")
                sock.connect((self.config['server_addr'], self.config['server_port']))
                sock.settimeout(None)
                
                # Autenticar
                if not self.authenticate(sock):
                    sock.close()
                    time.sleep(5)
                    continue
                
                # Criar proxy
                if not self.create_proxy(sock):
                    sock.close()
                    time.sleep(5)
                    continue
                
                print("✅ Tunnel estabelecido! Aguardando conexões...")
                print(f"🌐 Sua aplicação está disponível em:")
                print(f"   URL: {self.config['server_addr']}:{self.config['server_port']}")
                print(f"   Ou use: http://{self.config['server_addr']}:{self.config['server_port']}")
                print("\n📊 Status: Conectado | Ctrl+C para parar")
                
                # Loop principal de conexões
                while self.running:
                    try:
                        msg_type, data = self.recv_msg(sock)
                        
                        if msg_type is None:
                            print("❌ Conexão perdida com o servidor")
                            break
                        
                        if msg_type == 5:  # New connection
                            # Conectar à aplicação local
                            local_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            local_sock.settimeout(10)
                            
                            try:
                                local_sock.connect((self.config['local_ip'], self.config['local_port']))
                                local_sock.settimeout(None)
                                
                                # Gerar ID único para a conexão
                                self.connection_id += 1
                                conn_id = self.connection_id
                                
                                # Iniciar thread para a conexão
                                thread = threading.Thread(
                                    target=self.handle_connection, 
                                    args=(local_sock, sock, conn_id)
                                )
                                thread.daemon = True
                                thread.start()
                                
                                self.connections[conn_id] = thread
                                print(f"🔗 Nova conexão estabelecida (#{conn_id})")
                                
                            except Exception as e:
                                print(f"❌ Erro ao conectar localmente: {e}")
                                local_sock.close()
                        
                    except socket.timeout:
                        continue
                    except Exception as e:
                        print(f"❌ Erro no loop principal: {e}")
                        break
                
                sock.close()
                print("🔄 Tentando reconectar em 5 segundos...")
                
            except KeyboardInterrupt:
                print("\n⏹️  Parando tunnel...")
                break
            except Exception as e:
                print(f"❌ Erro de conexão: {e}")
                time.sleep(5)
        
        self.running = False
        print("👋 Tunnel finalizado")
    
    def run(self):
        """Método principal"""
        self.display_banner()
        
        if not self.load_config():
            print("❌ Falha na configuração")
            return
        
        print("\n🎯 Iniciando tunnel em 3 segundos...")
        time.sleep(3)
        
        try:
            self.start_tunnel()
        except KeyboardInterrupt:
            print("\n⏹️  Parando CZ7 FRPC...")
            self.running = False

def main():
    # Verificar Python
    if sys.version_info < (3, 6):
        print("❌ Python 3.6 ou superior necessário")
        return
    
    client = CZ7FRPC()
    client.run()

if __name__ == "__main__":
    main()
