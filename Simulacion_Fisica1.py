import pygame
import math
import random
import sys

pygame.init()

ancho_pantalla = 1400
alto_pantalla = 900
fps = 30

pantalla = pygame.display.set_mode((ancho_pantalla, alto_pantalla), pygame.RESIZABLE)
pygame.display.set_caption("Simulación leyes de Newton")

COLOR_CIELO_DIA = (135, 206, 235)
COLOR_CIELO_CREPU = (50, 100, 160)
COLOR_ESPACIO = (3, 3, 10)
COLOR_TIERRA = (120, 80, 40)
COLOR_CUERPO = (180, 60, 20)
COLOR_NARIZ = (140, 40, 10)
COLOR_LLAMAS_ACTIVAS = (255, 220, 50)
COLOR_LLAMAS_RESIDUO = (255, 120, 0)
COLOR_HUMO = (140, 140, 140)
COLOR_ESTRELLAS = (255, 255, 240)
COLOR_NUBE = (255, 255, 255)
COLOR_SATELITE = (200, 200, 200)
COLOR_HUD_FONDO = (0, 0,0)
COLOR_TEXTO_HUD = (255, 255, 255)
COLOR_ALERTA_HUD = (255, 0, 0)
COLOR_INFORME_HUD = (200, 230, 255)
COLOR_BARRA_PROGRESO = (50, 255, 50)
COLOR_INPUT_FONDO = (0, 0, 60)
COLOR_CURSOR = (255, 0, 0)
COLOR_TEXTO_INPUT = (250, 255, 252)
Proyecto_fisica_1= "__main__"

fuente_titulo = pygame.font.SysFont('Times New Roman', 18, True)
fuente_texto = pygame.font.SysFont('Times New Roman', 18)
fuente_input = pygame.font.SysFont('Times New Roman', 18)

ancho_cohete = 100
alto_cohete = 220
escala_altura = 1.0

masa_sin_combustible = 1000.0
masa_comb = 1000.0
vel_expulsion = 3000.0
consumo_masa = 20.0

fuerza_base = vel_expulsion * consumo_masa

cant_particulas_humo = 50
alt_revelacion = 2000
alt_espacio = 7000
alt_nubes_min = 0
alt_nubes_max = 6000

factor_camara = 0.4

ancho_hud = 650
posicion_hud_y = (alto_pantalla // 2) + 100

intensidad_shake = 4
duracion_llamas = 8

def limitar_color(c):
    return max(0, min(255, int(c)))

def dibujar_tierra_y_arboles(pantalla, cam_y):
    suelo_y = alto_pantalla - 80  # Altura fija suelo en pantalla

    # Tierra
    pygame.draw.rect(pantalla, COLOR_TIERRA, (0, suelo_y, ancho_pantalla, 80))

    # Arboles
    spacing = 100
    for x in range(50, ancho_pantalla, spacing):
        # Tronco
        pygame.draw.rect(pantalla, (80, 50, 20), (x, suelo_y - 40, 10, 40))
        # Copa
        puntos = [(x - 15, suelo_y - 40), (x + 25, suelo_y - 40), (x + 5, suelo_y - 80)]
        pygame.draw.polygon(pantalla, (0, 150, 0), puntos)

def limitar_valores(valor, minimo, maximo):
    return max(minimo, min(maximo, float(valor)))

def crear_particulas():
    lista = []
    for _ in range(cant_particulas_humo):
        lista.append({
            'x': 0,
            'y': 0,
            'vx': 0,
            'vy': 0,
            'vida': 0,
            'max_vida': random.randint(12,20),
            'tam': random.uniform(2.5,6.0),
            'visible': False
        })
    return lista

class Cohete:
    def __init__(self):
        self.particulas = crear_particulas()
        self.masa_sin_combustible = masa_sin_combustible
        self.masa_comb = masa_comb # Tasa de flujo de combustible
        self.vel_exp = vel_expulsion  #Velocidad de expulsion de gases
        self.consum_masa = consumo_masa
        self.comb_actual = self.masa_comb
        self.masa_total_inicial = self.masa_sin_combustible + self.masa_comb
        self.fuerza = self.vel_exp * self.consum_masa #Fuerza del motor (Velocidad de salida de gases * Tasa de flujo del combustible)
        self.pausa_auto = 0.0
        self.x = ancho_pantalla // 4
        self.y = alto_pantalla - 80 - alto_cohete
        self.vel_y = 0.0
        self.altura = 0.0
        self.acel = 0.0
        self.Cambio_de_velocidad = 0.0
        self.impulso_activo = False
        self.tiempo_total = 0.0
        self.shake_x = 0
        self.shake_y = 0
        self.tiempo_llama = 0
        self.Cambio_de_velocidad_max = 0.0
        self.actualizar_parametros(self.masa_sin_combustible, self.masa_comb, self.vel_exp, self.consum_masa, self.pausa_auto)
                # En __init__ de la clase cohete
        try:
            self.imagen_original = pygame.image.load("cohete.png").convert_alpha()
        except Exception as e:
            self.imagen_original = None  # si no existe la imagen usamos dibujo por defecto
        self.imagen_escalada = None
        self._ultima_size = (0, 0)
        # --- en __init__ ---
        # Intentar cargar varios frames: fuego_0.png, fuego_1.png, ...
        self.img_impulso_frames = []
        for i in range(8):  # hasta 8 frames (0..7)
            try:
                img = pygame.image.load(f"fuego_{i}.png").convert_alpha()
                self.img_impulso_frames.append(img)
            except Exception:
                break

    def reiniciar(self):
        self.x = ancho_pantalla // 4
        self.y = self.y = alto_pantalla - 80 - alto_cohete
        self.vel_y = 0.0
        self.altura = 0.0
        self.acel = 0.0
        self.Cambio_de_velocidad = 0.0
        self.impulso_activo = False
        self.tiempo_total = 0.0
        self.comb_actual = self.masa_comb
        self.shake_x = 0
        self.shake_y = 0
        self.tiempo_llama = 0
        for p in self.particulas:
            p['visible'] = False
            p['vida'] = 0

    def actualizar_parametros(self, m_dry, m_fuel, v_e, dm_dt, auto_pausa=0.0):
        # Solo acepta valores estrictamente positivos, ignorando otros sin clamping duro
        if m_dry > 0:
            self.masa_sin_combustible = m_dry
        if m_fuel > 0:
            self.masa_comb = m_fuel
        if v_e > 0:
            self.vel_exp = v_e
        if dm_dt > 0:
            self.consum_masa = dm_dt
        if auto_pausa >= 0:
            self.pausa_auto = auto_pausa

        self.fuerza = self.vel_exp * self.consum_masa #Fuerza del motor (Velocidad de salida de gases * Tasa de flujo del combustible)
        self.masa_total_inicial = self.masa_sin_combustible + self.masa_comb

        if not self.impulso_activo:
            self.comb_actual = self.masa_comb

        if self.masa_total_inicial > self.masa_sin_combustible and self.masa_sin_combustible > 0:
            self.Cambio_de_velocidad_max = self.vel_exp * math.log(self.masa_total_inicial / self.masa_sin_combustible)
        else:
            self.Cambio_de_velocidad_max = 0.0
        print(f"Parámetros nuevos: \nMasa sin combustible = {self.masa_sin_combustible}\n Masa del combustible = {self.masa_comb}\n Velocidad de escape de gases = {self.vel_exp}\n Tasa de consumo de combustible = {self.consum_masa}\n Fuerza = {self.fuerza}\n Velocidad de cambio = {self.Cambio_de_velocidad_max}\n Creado por JAIR")

    def emitir_humo(self):
        tasa = min(1.0, self.consum_masa / 20.0)
        for p in self.particulas:
            if not p['visible'] and random.random() < tasa:
                p['x'] = self.x + ancho_cohete//2 + random.uniform(-ancho_cohete//2, ancho_cohete//2)
                p['y'] = self.y + alto_cohete
                p['vx'] = random.uniform(-self.consum_masa/10, self.consum_masa/10)
                p['vy'] = random.uniform(2,5)
                p['vida'] = p['max_vida']
                p['visible'] = True
                p['tam'] = random.uniform(2,5)
                break

    def actualizar_particulas(self, dt):
        for p in self.particulas:
            if p['visible']:
                p['x'] += p['vx'] * dt * 60
                p['y'] += p['vy'] * dt * 60
                p['vy'] += 0.1 * dt * 60
                p['vida'] -= 1
                p['tam'] *= 0.99
                if p['vida'] <= 0 or p['tam'] < 0.5:
                    p['visible'] = False

    def actualizar_fisica(self, dt, empuje_presionado, pausado):
        if pausado:
            return
        masa_actual = self.masa_sin_combustible + self.comb_actual #Masa actual es (mas sin conbustible + masa del combustible)
        self.impulso_activo = False
        if empuje_presionado and self.comb_actual > 0:
            self.impulso_activo = True
            self.tiempo_llama = duracion_llamas
            quemado = self.consum_masa * dt # Consumo de masa  por el tiempo transcurrido 
            self.comb_actual = max(0, self.comb_actual - quemado) # Combustible actual 
            masa_actual = self.masa_sin_combustible + self.comb_actual
            self.acel = self.fuerza / masa_actual if masa_actual > 0 else 0  #Aceleracion
            dv = self.acel * dt # Cambio de velocidad en funcion del tiempo  (aceleracion por tiempo)
            self.vel_y -= dv
            self.Cambio_de_velocidad += dv #Acumulador de velocidad
            self.emitir_humo()
            if self.tiempo_total < 20:
                intensidad = intensidad_shake * (self.comb_actual / self.masa_comb)
                intensidad_ent = max(1, int(intensidad))
                self.shake_x = random.randint(-intensidad_ent, intensidad_ent)
                self.shake_y = random.randint(-intensidad_ent//2, intensidad_ent//2)
            self.tiempo_total += dt
        else:
            if self.tiempo_llama > 0:
                self.tiempo_llama -= 1
            else:
                self.shake_x = 0
                self.shake_y = 0
            self.acel = 0
        self.y += self.vel_y * dt
        self.altura = max(0, alto_pantalla - self.y - (80 + alto_cohete)) * escala_altura
        self.actualizar_particulas(dt)

    def dibujar(self, pantalla, cam_y):
        x_d = self.x + self.shake_x
        y_d = (self.y - cam_y) + self.shake_y
        if y_d < -alto_cohete*2 or y_d > alto_pantalla + alto_cohete*2:
            return

        # ----------------------------
        # 1) Intentamos dibujar la imagen escalada del cohete
        # ----------------------------
        if getattr(self, "imagen_original", None):
            # escalamos solo si la última size no coincide (optimización)
            target_size = (int(ancho_cohete), int(alto_cohete))
            if self.imagen_escalada is None or self._ultima_size != target_size:
                # mantener proporción exacta o forzar tamaño según ancho/alto variables
                self.imagen_escalada = pygame.transform.smoothscale(self.imagen_original, target_size)
                self._ultima_size = target_size

            # obtener rect en topleft para que coincida con tus coords x_d,y_d
            cohete_rect = self.imagen_escalada.get_rect(topleft=(int(x_d), int(y_d)))
            pantalla.blit(self.imagen_escalada, cohete_rect)
        else:
            # ----------------------------
            #  Fallback: dibujo original con rects/poligonos si no hay imagen
            # ----------------------------
            pygame.draw.rect(pantalla, COLOR_CUERPO, (x_d, y_d, ancho_cohete, alto_cohete))
            pygame.draw.rect(pantalla, COLOR_NARIZ, (x_d, y_d, ancho_cohete, alto_cohete//2))
            puntos_nariz = [(x_d, y_d), (x_d+ancho_cohete, y_d), (x_d+ancho_cohete//2, y_d-15)]
            pygame.draw.polygon(pantalla, COLOR_NARIZ, puntos_nariz)

            alto_aletas = 12
            pygame.draw.polygon(pantalla, COLOR_CUERPO, [(x_d, y_d+alto_cohete), (x_d-6, y_d+alto_cohete+alto_aletas), (x_d+6, y_d+alto_cohete+alto_aletas//2)])
            pygame.draw.polygon(pantalla, COLOR_CUERPO, [(x_d+ancho_cohete, y_d+alto_cohete), (x_d+ancho_cohete+6, y_d+alto_cohete+alto_aletas), (x_d+ancho_cohete-6, y_d+alto_cohete+alto_aletas//2)])

        # ----------------------------
        # 2) Llamas (se mantienen igual)
        # ----------------------------
        if self.impulso_activo or self.tiempo_llama > 0:
            llama_y = y_d + alto_cohete
            llama_len = 30 + int(self.fuerza / 2000)
            intensidad = 1.0 if self.impulso_activo else (self.tiempo_llama / duracion_llamas)
            colo_base = COLOR_LLAMAS_ACTIVAS if self.comb_actual > 0 else COLOR_LLAMAS_RESIDUO
            for i in range(5):
                seg_y = llama_y + (i * llama_len / 5)
                ondula = math.sin(self.tiempo_total * 20 + i) * 4 * intensidad
                puntos = [
                    (x_d + ancho_cohete//2 + ondula, seg_y),
                    (x_d + ondula*0.5, seg_y + (llama_len / 5)),
                    (x_d + ancho_cohete + ondula*0.5, seg_y + (llama_len / 5))
                ]
                color_final = tuple(limitar_color(c * intensidad) for c in colo_base)
                pygame.draw.polygon(pantalla, color_final, puntos)

        # ----------------------------
        # 3) Partículas/humo (idéntico a tu código)
        # ----------------------------
        for p in self.particulas:
            if p['visible']:
                py = p['y'] - cam_y
                if -20 < py < alto_pantalla + 20:
                    alpha = p['vida'] / p['max_vida']
                    color_humo = tuple(limitar_color(c * alpha) for c in COLOR_HUMO)
                    tamano = max(1, int(p['tam'] * alpha))
                    pygame.draw.circle(pantalla, color_humo, (int(p['x']), int(py)), tamano)
                    for j in range(3):
                        t_alpha = alpha * (1 - j * 0.35)
                        t_tamano = max(1, tamano - j * 1)
                        t_x = p['x'] - p['vx'] * j * 3.5
                        t_y = py + p['vy'] * j * 3.5
                        t_col = tuple(limitar_color(c * t_alpha) for c in COLOR_HUMO)
                        pygame.draw.circle(pantalla, t_col, (int(t_x), int(t_y)), t_tamano)

class Entorno:
    def __init__(self):
        self.suelo_y = alto_pantalla
        self.altura_suelo = 80
        self.x_plataforma = ancho_pantalla // 4
        self.estrellas = self.generar_estrellas(150)
        self.nubes = self.generar_nubes(100)
        self.satelites = self.generar_satelites(5)
        self.tiempo_nubes = 0

    def generar_estrellas(self, cantidad):
        return [(random.randint(0, ancho_pantalla*2), random.randint(0, alto_pantalla*2)) for _ in range(cantidad)]

    def generar_nubes(self, cantidad):
        lista = []
        for _ in range(cantidad):
            lista.append({
                'x': random.uniform(0, ancho_pantalla*2),
                'y': random.uniform(alt_nubes_min, alt_nubes_max),
                'tam': random.uniform(40, 80),
                'vel': random.uniform(0.5, 1.5),
                'opacidad': 1.0
            })
        return lista

    def generar_satelites(self, cantidad):
        lista = []
        for _ in range(cantidad):
            lista.append({
                'x': random.uniform(0, ancho_pantalla*2),
                'y': random.uniform(2000,6000),
                'tam': random.uniform(8,15),
                'vel': random.uniform(1.0, 3.0),
                'angulo': random.uniform(0, 360),
                'rad_orbita': random.uniform(50,100)
            })
        return lista

    def actualizar_y_dibujar_fondo(self, pantalla, altura, cam_y, dt):
        progreso = min(altura / alt_espacio, 1.0)
        self.tiempo_nubes += dt

        # Dibujo del cielo y estrellas
        if altura < alt_revelacion:
            for y in range(alto_pantalla):
                ratio = y / alto_pantalla
                r = limitar_color(COLOR_CIELO_DIA[0] * (1 - ratio*0.3))
                g = limitar_color(COLOR_CIELO_DIA[1] * (1 - ratio*0.3))
                b = limitar_color(COLOR_CIELO_DIA[2] + 40 * ratio)
                pygame.draw.line(pantalla, (r,g,b), (0,y), (ancho_pantalla,y))
        elif altura < alt_espacio:
            factor_reveal = (altura - alt_revelacion) / (alt_espacio - alt_revelacion)
            for y in range(alto_pantalla):
                ratio = y / alto_pantalla
                r = limitar_color(COLOR_CIELO_CREPU[0] * (1-factor_reveal) + COLOR_ESPACIO[0] * factor_reveal)
                g = limitar_color(COLOR_CIELO_CREPU[1] * (1-factor_reveal) + COLOR_ESPACIO[1] * factor_reveal)
                b = limitar_color(COLOR_CIELO_CREPU[2] * (1-factor_reveal) + COLOR_ESPACIO[2] * factor_reveal)
                pygame.draw.line(pantalla,(r,g,b),(0,y),(ancho_pantalla,y))
        else:
            pantalla.fill(COLOR_ESPACIO)
            for x_star, y_star in self.estrellas:
                y_dib = (y_star - cam_y*0.2) % (alto_pantalla*2)
                if 0 < y_dib < alto_pantalla:
                    brillo = math.sin(self.tiempo_nubes*5 + x_star)*0.5 + 0.5
                    color_estrella = tuple(limitar_color(c*brillo) for c in COLOR_ESTRELLAS)
                    pygame.draw.circle(pantalla, color_estrella, (int(x_star % ancho_pantalla), int(y_dib)), 1)

        # Suelo
        suelo_y_dib = self.suelo_y - cam_y

        # Efecto de arboles
        max_alt_desaparicion = 1500
        factor_visibilidad = max(0, 1 - altura / max_alt_desaparicion)
        altura_visible_suelo = int(80 * factor_visibilidad)

        if altura_visible_suelo > 0:
            suelo_y = alto_pantalla - altura_visible_suelo
            pygame.draw.rect(pantalla, COLOR_TIERRA, (0, suelo_y, ancho_pantalla, altura_visible_suelo))

            spacing = 100
            for x in range(50, ancho_pantalla, spacing):
                tronco_alto = int(40 * factor_visibilidad)
                copa_alto = int(40 * factor_visibilidad)
                pygame.draw.rect(pantalla, (80, 50, 20), (x, suelo_y - tronco_alto, 10, tronco_alto))
                puntos_copa = [(x - 15, suelo_y - tronco_alto), (x + 25, suelo_y - tronco_alto), (x + 5, suelo_y - tronco_alto - copa_alto)]
                pygame.draw.polygon(pantalla, (0, 150, 0), puntos_copa)

        # Nubes a 200 
        if altura > 0:
            opacidad_nubes = max(0, 1 - (altura- 200) / (alt_espacio - 200) * 0.8)
            for nube in self.nubes:
                nube['x'] -= nube['vel'] * 30 * dt
                if nube['x'] < -nube['tam']:
                    nube['x'] = ancho_pantalla + nube['tam']
                y_dib = nube['y'] - cam_y
                if 0 < y_dib < alto_pantalla and opacidad_nubes > 0:
                    alpha = int(255 * opacidad_nubes * 0.8)
                    color_nube_calc = tuple(limitar_color(c * alpha / 255) for c in COLOR_NUBE)
                    offsets = [(-10,0), (0,0), (10,0), (5,-5), (-5,-5)]
                    for ox, oy in offsets:
                        pygame.draw.circle(pantalla, color_nube_calc, (int(nube['x'] + ox), int(y_dib + oy)), int(nube['tam'] // 3))

        # Satelites
        if alt_revelacion <= altura < alt_espacio:
            vis_satelite = (altura - alt_revelacion) / (alt_espacio - alt_revelacion)
            for sat in self.satelites:
                sat['x'] -= sat['vel'] * 20 * dt
                if sat['x'] < -sat['tam']:
                    sat['x'] = ancho_pantalla + sat['tam']
                sat['angulo'] += sat['vel'] * 2 * dt
                orb_x = sat['x'] + math.cos(sat['angulo']) * sat['rad_orbita']
                orb_y = (sat['y'] - cam_y) + math.sin(sat['angulo']) * (sat['rad_orbita']/2)
                if 0 < orb_y < alto_pantalla and vis_satelite > 0.2:
                    alpha_sat = int(255 * vis_satelite)
                    color_sat = tuple(limitar_color(c * alpha_sat / 255) for c in COLOR_SATELITE)
                    pygame.draw.rect(pantalla, color_sat, (int(orb_x - sat['tam']/2), int(orb_y - sat['tam']/4), int(sat['tam']), int(sat['tam']/2)))
                    pygame.draw.line(pantalla, color_sat, (int(orb_x), int(orb_y - sat['tam']/4)), (int(orb_x), int(orb_y - sat['tam'])), 2)

        # Plataforma
        if suelo_y_dib < alto_pantalla:
            alpha_suelo = max(0, 1 - altura / alt_revelacion)
            color_suelo_calc = tuple(limitar_color(c * alpha_suelo) for c in COLOR_TIERRA)
            pygame.draw.rect(pantalla, color_suelo_calc, (0, suelo_y_dib, ancho_pantalla, self.altura_suelo))
            if alpha_suelo > 0.1:
                color_plataforma = tuple(limitar_color(c * alpha_suelo) for c in (150,150,150))
                y_plat = suelo_y_dib - 10
                pygame.draw.rect(pantalla, color_plataforma, (self.x_plataforma - 30, y_plat, 60, 10))

    def dibujar(self, pantalla, altura, cam_y, dt):
        self.actualizar_y_dibujar_fondo(pantalla, altura, cam_y, dt)

def main():
    global ancho_pantalla, alto_pantalla, pantalla
    reloj = pygame.time.Clock()
    cohete = Cohete()
    entorno = Entorno()
    
    pos_hud_x = ancho_pantalla - ancho_hud - 100  
    pos_hud_y = posicion_hud_y
    arrastrando_hud = False
    offset_x_click = 0
    offset_y_click = 0
    pausado = True
    ejecutando = True
    dt = 0
    estado = "Pausado - 'I' para iniciar; 'P' para pausa/editar."
    imp_btn_presionado = False
    cam_y = cohete.y - (alto_pantalla - 80 - alto_cohete)
    contador_ciclos = 0
    pausado_auto = False

    campo_edicion = 0
    buffer_entrada = ["1000", "1000", "3000", "20", "0"] 
    cursor_visible = True
    tiempo_cursor = 0
    hud_y = (alto_pantalla - 600) // 2

    while ejecutando:
        dt = reloj.tick(fps)/1000.0
        tiempo_cursor += dt
        cursor_visible = (tiempo_cursor % 1.0) < 0.5

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                ejecutando = False
            elif evento.type == pygame.VIDEORESIZE:
                ancho_pantalla, alto_pantalla = evento.size
                pantalla = pygame.display.set_mode((ancho_pantalla, alto_pantalla), pygame.RESIZABLE)
                entorno = Entorno()
                cohete.reiniciar()
            elif evento.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                if pos_hud_x <= mx <= pos_hud_x + ancho_hud and pos_hud_y <= my <= pos_hud_y + 600:
                    arrastrando_hud = True
                    offset_x_click = mx - pos_hud_x
                    offset_y_click = my - pos_hud_y
            elif evento.type == pygame.MOUSEBUTTONUP:
                arrastrando_hud = False
            elif evento.type == pygame.MOUSEMOTION and arrastrando_hud:
                mx, my = pygame.mouse.get_pos()
                pos_hud_x = mx - offset_x_click
                pos_hud_y = my - offset_y_click
            elif evento.type == pygame.KEYDOWN:             
               
                
                if evento.key == pygame.K_i and pausado:
                    pausado = False
                    estado = "Simulación corriendo - presiona ESPACIO para empuje"
                elif evento.key == pygame.K_p:
                    pausado = not pausado
                    if pausado:
                        estado = "Pausado - Selecciona campo (W, E, F, G, T), escribe y ENTER para guardar"
                    else:
                        estado = "Reanudado - Cambios aplicados"
                elif evento.key == pygame.K_SPACE and not pausado:
                    imp_btn_presionado = True
                elif evento.key == pygame.K_r:
                    cohete = Cohete()
                    entorno = Entorno()
                    cam_y = cohete.y - (alto_pantalla - 80 - alto_cohete)
                    buffer_entrada = ["1000", "1000", "3000", "20", "0"]
                    campo_edicion = 0
                    pausado = True
                    pausado_auto = False
                    estado = "Reiniciado - 'I' para iniciar vuelo"
                
                elif evento.key == pygame.K_ESCAPE:
                    ejecutando = False


                elif pausado and evento.key in (pygame.K_w, pygame.K_e, pygame.K_f, pygame.K_g, pygame.K_t):
                    if evento.key == pygame.K_w:
                        campo_edicion = 1
                    elif evento.key == pygame.K_e:
                        campo_edicion = 2
                    elif evento.key == pygame.K_f:
                        campo_edicion = 3
                    elif evento.key == pygame.K_g:
                        campo_edicion = 4
                    elif evento.key == pygame.K_t:
                        campo_edicion = 5

                    estado = f"Editando campo {campo_edicion}: {buffer_entrada[campo_edicion-1]}; escribe y ENTER"
                elif pausado and evento.key == pygame.K_RETURN:
                    if campo_edicion > 0:
                        try:
                            val = float(buffer_entrada[campo_edicion-1])
                            if campo_edicion == 1:
                                cohete.actualizar_parametros(val, cohete.masa_comb, cohete.vel_exp, cohete.consum_masa, cohete.pausa_auto)
                            elif campo_edicion == 2:
                                cohete.actualizar_parametros(cohete.masa_sin_combustible, val, cohete.vel_exp, cohete.consum_masa, cohete.pausa_auto)
                            elif campo_edicion == 3:
                                cohete.actualizar_parametros(cohete.masa_sin_combustible, cohete.masa_comb, val, cohete.consum_masa, cohete.pausa_auto)
                            elif campo_edicion == 4:
                                cohete.actualizar_parametros(cohete.masa_sin_combustible, cohete.masa_comb, cohete.vel_exp, val, cohete.pausa_auto)
                            elif campo_edicion == 5:
                                cohete.actualizar_parametros(cohete.masa_sin_combustible, cohete.masa_comb, cohete.vel_exp, cohete.consum_masa, val)
                            buffer_entrada[campo_edicion-1] = f"{val:.1f}" if campo_edicion==5 else str(int(val))
                            campo_edicion = 0
                            estado = "Parámetro guardado - Presiona P para continuar"
                        except:
                            estado = "Error: Ingresa valor correcto"
                elif pausado and campo_edicion > 0 and (evento.unicode.isdigit() or evento.unicode in '.-'):
                    buffer_entrada[campo_edicion-1] += evento.unicode
                elif pausado and evento.key == pygame.K_BACKSPACE and campo_edicion > 0:
                    buffer_entrada[campo_edicion-1] = buffer_entrada[campo_edicion-1][:-1]

            elif evento.type == pygame.KEYUP:
                if evento.key == pygame.K_SPACE:
                    imp_btn_presionado = False

        if not pausado:
            cohete.actualizar_fisica(dt, imp_btn_presionado, pausado)
        
            if cohete.pausa_auto > 0 and cohete.tiempo_total >= cohete.pausa_auto and not pausado_auto:
                pausado = True
                pausado_auto = True
                estado = f"Pausado automáticamente en T+{cohete.tiempo_total:.1f} s"
            min_altura_para_mover_camara = 450
            if cohete.altura > min_altura_para_mover_camara:                
                cam_objetivo = cohete.y - (alto_pantalla * factor_camara)
                cam_y += (cam_objetivo - cam_y) * min(8.0 * dt, 1.0)
            else:
                cam_y = 0


            tiempo_actual = cohete.tiempo_total
            if imp_btn_presionado and cohete.comb_actual > 0:
                estado = f"T+{tiempo_actual:.1f}s - Acelerando (a={cohete.acel:.2f} m/s²)"
            elif tiempo_actual > 0:
                if cohete.comb_actual > 0:
                    estado = f"T+{tiempo_actual:.1f}s - Vuelo con empuje (v={cohete.Cambio_de_velocidad/1000:.2f} km/min)"
                else:
                    estado = f"T+{tiempo_actual:.1f}s - Caída libre (fuel agotado, v={abs(cohete.vel_y):.1f} m/s)"
            else:
                estado = "Esperando empuje - presiona ESPACIO"

            if cohete.comb_actual < 100:
                estado += f" - Combustible: {cohete.comb_actual:.0f} kg"
        entorno.actualizar_y_dibujar_fondo(pantalla, cohete.altura, cam_y, dt)
        cohete.dibujar(pantalla, cam_y)
        entorno.dibujar(pantalla, cohete.altura, cam_y, dt)
        cohete.dibujar(pantalla, cam_y)

        hud_x = ancho_pantalla - ancho_hud
        hud_alto = 610
        hud = pygame.Surface((ancho_hud, hud_alto))
        hud.fill(COLOR_HUD_FONDO)
        pygame.draw.rect(hud, COLOR_TEXTO_HUD, (0,0,ancho_hud,hud_alto), 2)

        y_text = 5
        titulo = fuente_titulo.render("Simulación leyes de Newton", True, COLOR_TEXTO_HUD)
        hud.blit(titulo, (5, y_text))
        y_text += 25

        metricas = [
            f"Tiempo: {cohete.tiempo_total:.1f} s",
            #f"Altitud: {(cohete.altura/1000):.3f} km",cohete.Cambio_de_velocidad_max
            f"Velocidad: {abs(cohete.vel_y):.2f} m/s ({abs(cohete.vel_y*3.6):.3f} km/h)",
            f"Aceleración: {cohete.acel:.2f} m/s²",
            f"Empuje: {cohete.fuerza:.0f} N",
            f"Cambio de velocidad:: {cohete.Cambio_de_velocidad*3.6 :.3f} km/h (Máx: {cohete.Cambio_de_velocidad_max*3.6:.3f} km/h)",
            f"Masa Actual: {cohete.masa_sin_combustible + cohete.comb_actual:.0f} kg",
            f"Combustible Restante: {cohete.comb_actual:.0f} kg ({cohete.comb_actual / cohete.masa_comb * 100:.1f}%)",
            f"Auto-Pausa: {cohete.pausa_auto:.1f} s" if cohete.pausa_auto > 0 else "Auto-Pausa: Desactivada",
            f"Estado: {estado}"
        ]

        for m in metricas:
            color_texto = COLOR_ALERTA_HUD if ('CRÍTICO' in m or cohete.comb_actual < 100) else COLOR_INFORME_HUD
            if 'Altitud' in m or 'Velocidad' in m:
                color_texto = COLOR_BARRA_PROGRESO
            texto_surf = fuente_texto.render(m, True, color_texto)
            hud.blit(texto_surf, (5, y_text))
            y_text += 18

        if pausado:
            y_text += 10
            gui_titulo = fuente_titulo.render("EDITAR PARAMETROS (Pausa)", True, COLOR_ALERTA_HUD)
            hud.blit(gui_titulo, (5, y_text))
            y_text += 25
            campos = [
                ("W. Masa sin combustible (kg):", buffer_entrada[0]),
                ("E. Masa combustible (kg):", buffer_entrada[1]),
                ("F. Velocidad de escape de gases (m/s):", buffer_entrada[2]),
                ("G. Tasa de consumo de combustible (kg/s):", buffer_entrada[3]),
                ("T. Auto-pausa (seg):", buffer_entrada[4])
            ]
            for i, (label, buf) in enumerate(campos, 1):
                activo = (campo_edicion == i)
                col_label = COLOR_TEXTO_HUD if not activo else COLOR_ALERTA_HUD
                lbl_surf = fuente_texto.render(label, True, col_label)
                hud.blit(lbl_surf, (5, y_text))
                rect_input = pygame.Rect(5, y_text+20, 120, 20)
                col_rect = COLOR_INPUT_FONDO if not activo else COLOR_ALERTA_HUD
                pygame.draw.rect(hud, col_rect, rect_input)
                pygame.draw.rect(hud, COLOR_TEXTO_HUD, rect_input, 1)
                txt_surf = fuente_input.render(buf, True, COLOR_TEXTO_INPUT)
                hud.blit(txt_surf, (rect_input.x + 5, rect_input.y + 2))

                if activo and cursor_visible and len(buf) < 10:
                    cursor_x = rect_input.x + 5 + txt_surf.get_width() + 2
                    pygame.draw.line(hud, COLOR_CURSOR, (cursor_x, rect_input.y+2), (cursor_x, rect_input.y+18), 2)

                y_text += 40
            y_text += 5
            instr_surf = fuente_texto.render("ENTER: Guardar | Backspace: Borrar | Editar parametros (W, E, F, G, T): Seleccionar", True, (200,200,100))
            hud.blit(instr_surf, (5, y_text))
        else:
            y_text += 10
            titulo_valores = fuente_titulo.render("PARAMETROS ACTIVOS", True, COLOR_INFORME_HUD)
            hud.blit(titulo_valores, (5, y_text))
            y_text += 25
            valores = [
                f"Masa sin combustible: {cohete.masa_sin_combustible:.0f} kg",
                f"Masa combustible inicial: {cohete.masa_comb:.0f} kg",
                f"Velocidad expulsión: {cohete.vel_exp:.0f} m/s",
                f"Consumo masa: {cohete.consum_masa:.1f} kg/s",
                f"Auto-pausa: {cohete.pausa_auto:.1f} s" if cohete.pausa_auto > 0 else "Auto-pausa: Desactivada",
                f"Empuje: {cohete.fuerza:.0f} N",
                f"Cambio máximo de velocidad: {cohete.Cambio_de_velocidad_max * 3.6 :.2f} km/h"
            ]
            for val in valores:
                surf = fuente_texto.render(val, True, COLOR_INFORME_HUD)
                hud.blit(surf, (5, y_text))
                y_text += 18

        y_text += 20
        titulo_controles = fuente_titulo.render("CONTROLES", True, (255,255,0))
        hud.blit(titulo_controles, (5, y_text))
        y_text += 22
        lista_controles = [
            "I: Iniciar",
            "P: Pausa/Editar",
            "Editar parametros (W, E, F, G, T): Seleccionar campo (pausa)",
            "Espacio: Empuje",
            "R: Reiniciar",
            "ESC: Salir",
            f"Ciclos: {contador_ciclos}"
        ]
        for ct in lista_controles:
            txt = fuente_texto.render(ct, True, (220,220,120))
            hud.blit(txt, (5, y_text))
            y_text += 16

        pantalla.blit(hud, (pos_hud_x, pos_hud_y))
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if Proyecto_fisica_1 == "__main__":
    main()
