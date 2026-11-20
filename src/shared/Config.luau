--!strict
--[[
	Constantes de gameplay. Nenhum número mágico fora deste arquivo.
	Valores iniciais para playtest; serão ajustados nos testes (e por boosts, ADR 0025).
]]

local Config = {
	-- Câmera lateral 2.5D (ADR 0011, 0038).
	Camera = {
		Distance = 64, -- distância da câmera até o plano; com FOV 50 mostra ~60 studs de altura
		Height = 6, -- quanto a câmera fica acima do personagem
		LookAhead = 6, -- studs que a câmera adianta na direção em que o personagem anda
		LookAheadSpeed = 38, -- studs/s em X a partir dos quais o adiantamento é total (velocidade de andar)
		FieldOfView = 50,
		Smoothing = 10, -- maior = segue mais rápido
	},

	-- Plano onde todo o jogo acontece (ADR 0011).
	Plane = {
		Z = 0,
		MaxDrift = 0.05, -- desvio em Z tolerado no cliente antes de corrigir (CharacterController)
		-- Correção no servidor (ADR 0039, PlaneService). A posição replicada chega atrasada e
		-- interpolada, então o servidor tolera mais que o cliente.
		ServerMaxDrift = 0.5, -- studs
		ServerCheckInterval = 0.1, -- segundos entre as conferências
	},

	-- Movimento base do jogador (ADR 0043, RF-03; MovementController).
	Movement = {
		-- Inspirado no DDNet (medido no vídeo de referência), num meio-termo com a escala do jogo:
		-- gravidade do DDNet (a mesma do gancho), andar e pulos um pouco menores que os do DDNet.
		Gravity = 112.5, -- studs/s² no jogo todo (DDNet: 0,5 unidade/tick²; Roblox padrão: 196,2)
		WalkSpeed = 38, -- studs/s (DDNet fiel seria 45; padrão do Roblox: 16)
		JumpPower = 51, -- studs/s de saída do pulo do chão: ~11,5 studs de altura, ~0,9 s no ar
		DoubleJumpVelocity = 48, -- studs/s para cima no pulo duplo (a queda é zerada antes): ~+10 studs
		-- Tempo mínimo no ar antes do pulo duplo valer (não dispara junto com o primeiro pulo).
		DoubleJumpMinAirTime = 0.12, -- segundos
		-- Pedidos de pulo mais próximos que isto contam como o mesmo aperto (tecla segurada repete).
		JumpRequestRepeatGap = 0.1, -- segundos
		-- Atributo (só local) no personagem: true enquanto o gancho controla o corpo (preso ou embalo).
		HookActiveAttribute = "HookActive",
	},

	Checkpoint = {
		ZoneHeight = 10, -- studs acima da peça em que o checkpoint ainda conta
		SpawnHeight = 4, -- studs acima da peça onde o jogador renasce
	},

	Race = {
		RespawnTime = 1, -- segundos entre morrer e renascer
		-- Altura acima da peça RaceFinish em que a chegada ainda conta (como Checkpoint.ZoneHeight).
		FinishZoneHeight = 10, -- studs
		ActionCooldown = 1, -- segundos mínimos entre dois pedidos "Again"/"Lobby" do mesmo jogador
	},

	-- Lobby antes do mapa (ADR 0044).
	Lobby = {
		PortalMargin = 1, -- studs de folga em volta do portal em que entrar ainda conta
		CheckInterval = 0.1, -- segundos entre as conferências do portal
	},

	Hook = {
		-- "DDNet" = física do gancho do DDNet (padrão). "Pull" = puxão direto (ADR 0042) e "Swing" =
		-- RopeConstraint (ADR 0036), mantidos como referência.
		Mode = "DDNet",
		Range = 40, -- studs, contados do HumanoidRootPart (ADR 0039)
		Cooldown = 0.1, -- segundos entre um prender e o próximo
		-- Esfera de ajuda de mira (ADR 0039). 0 = desligada: o gancho segue exatamente a linha da mira.
		AimAssistRadius = 0, -- studs

		-- Modo "DDNet". Tuning padrão do DDNet (50 ticks/s) com 1 unidade/tick = 4,5 studs/s (um pouco
		-- acima da escala do pulo deste jogo, 3,8, para o gancho ficar mais rápido como no DDNet).
		TickRate = 50, -- ticks/s de referência do gancho e do controle no ar
		FireSpeed = 360, -- studs/s do gancho voando (80 unidades/tick)
		DragAccel = 675, -- studs/s² do puxão (3,0 unidades/tick²)
		-- Gravidade do DDNet (0,5 unidade/tick²) enquanto o gancho controla o corpo (preso e embalo).
		-- A do Roblox (196,2) é 1,74x mais forte nesta escala e encurtava a parábola.
		HookGravity = 112.5, -- studs/s²
		DragSpeed = 68, -- studs/s: o puxão só acelera até aqui (15 unidades/tick)
		DragMinDistance = 4.8, -- studs: mais perto do ponto que isso não puxa (46 unidades)
		DragDownFactor = 0.3, -- puxão para baixo vale 30% (fica mais fácil subir numa plataforma)
		DragAssistFactor = 0.95, -- X do puxão com A/D no mesmo sentido
		DragResistFactor = 0.75, -- X do puxão sem A/D ou contra
		SurfaceTolerance = 0.5, -- studs: folga para o ponto atingido contar como "na peça, no plano"
		-- Peças com CanCollide = false (volumes de zona, enfeites) não prendem.
		IgnoreNonCollidable = true,

		-- Corda do balanço (RF-18; só modo "Swing")
		MinRopeLength = 4, -- studs
		MaxRopeLength = 45, -- studs; >= Range + AimAssistRadius, senão a corda dá um tranco ao prender
		ReelInSpeed = 18, -- studs/s ao segurar W
		ReelOutSpeed = 18, -- studs/s ao segurar S
		-- Ao recolher, o comprimento não fica mais que isso abaixo da distância real (puxão suave).
		ReelMaxLead = 0.75, -- studs
		-- Sonda contra atravessar paredes ao recolher: a caixa do corpo, deslocada estes studs na
		-- direção da corda; se tocar algo colidível, a corda para de encurtar.
		ReelProbeDistance = 0.5, -- studs
		ReelProbeInset = 0.2, -- studs que a caixa encolhe de cada lado (não acusar o chão em que pisa)

		-- Puxão (modo "Pull", ADR 0042)
		PullSpeed = 58, -- studs/s de cruzeiro até o alvo (o balanço testado chegava a ~78)
		PullAccel = 180, -- studs/s²: quão rápido a velocidade chega à de cruzeiro (e freia, se segurando)
		-- Força máxima do puxão, em studs/s² (vezes a massa) além da gravidade: folga para seguir a
		-- velocidade pedida sem empurrar demais contra o que estiver no caminho.
		PullMaxForceAccel = 400,
		ArriveDistance = 3, -- studs do ponto em que conta como "chegou"
		-- Segurando o botão, o puxão freia para parar no ponto; esta é a velocidade mínima da frenagem
		-- (sem ela, a aproximação final ficaria lenta demais).
		PullArriveSpeed = 12, -- studs/s
		-- Ao chegar sem o botão apertado, o gancho solta e sobra esta fração da velocidade (embalo).
		ReleaseMomentumFraction = 0.45,
		-- Prendeu no chão: pula para sair dele se o alvo não estiver muito para baixo (componente Y da
		-- direção do puxão maior que isto; -1..1).
		PullTakeOffMinUp = -0.3,
		HoldGain = 10, -- 1/s: quão firme o personagem fica no ponto enquanto segura o botão
		PullMaxTime = 1.5, -- segundos: se não chegar até lá (algo segurou), o gancho solta
		-- Sonda contra atravessar paredes no puxão: como `ReelProbeDistance`, mas na direção do voo.
		PullProbeDistance = 0.5, -- studs
		-- Se a sonda bater a até esta distância do ponto, conta como chegou (teto/parede do próprio alvo).
		PullBlockedArriveDistance = 6, -- studs

		-- Balanço (RF-17)
		-- Controle horizontal enquanto o gancho controla o corpo (preso e no embalo), como no DDNet.
		-- A/D aceleram até o limite sem cortar velocidade acima dele; sem A/D, o atrito freia por tick.
		AirControlAccel = 340, -- studs/s² (1,5 unidades/tick²)
		AirControlSpeed = 22, -- studs/s (5 unidades/tick)
		AirFriction = 0.95, -- fração do X mantida por tick no ar sem A/D
		GroundControlAccel = 450, -- studs/s² (2 unidades/tick²); limite = WalkSpeed do Humanoid
		GroundFriction = 0.5, -- fração do X mantida por tick no chão sem A/D (para firme)
		-- studs/s; limite horizontal enquanto preso e no embalo. Acima de DragSpeed para o embalo acumular.
		MaxSwingSpeed = 180,
		-- Quão rápido o personagem gira para ficar em pé / virar de lado enquanto preso (mais baixo = giro
		-- mais suave ao inverter o balanço).
		UprightResponsiveness = 20,
		FaceFlipSpeed = 6, -- studs/s em X para o personagem virar (evita virar a cada inversão lenta)
		-- Embalo depois de soltar: o Humanoid continua sem controle próprio (senão freia no ar) até
		-- tocar o chão, a velocidade horizontal cair até a de andar, ou passar este tempo.
		MomentumMaxTime = 3, -- segundos
		GroundCheckMargin = 0.6, -- studs abaixo dos pés que já contam como "no chão"

		-- Validação no servidor (HookService)
		ServerRangeTolerance = 10, -- studs a mais no alcance (atraso da posição replicada)
		ServerSurfaceTolerance = 2, -- studs de folga para o ponto estar na peça e no plano
		ServerCooldownSlack = 0.1, -- segundos de folga no intervalo entre prender (variação da rede)
		ServerMaxMessagesPerSecond = 20, -- limite de mensagens do gancho por jogador

		-- Visual (só local nesta fase)
		RopeThickness = 0.15,
		RopeColor = Color3.fromRGB(235, 225, 200),
		ReticleSize = 30, -- pixels do anel em volta do cursor
		ReticleMarkerSize = 10, -- pixels do ponto onde o gancho prenderia
		ReticleNoTargetColor = Color3.fromRGB(200, 200, 200),
		ReticleValidColor = Color3.fromRGB(90, 220, 255),
		ReticleForbiddenColor = Color3.fromRGB(255, 70, 70),
		ForbiddenFlashTime = 0.25, -- segundos que o retículo pisca ao tentar prender em superfície proibida
		ForbiddenFlashScale = 1.6, -- quanto o anel cresce ao piscar
	},

	-- Nomes de atributos replicados (SetAttribute) usados por mais de um módulo.
	Attributes = {
		Checkpoint = "Checkpoint", -- no Player: número do último checkpoint alcançado
		HookOnceEpoch = "HookOnceEpoch", -- no Player: muda quando o uso dos verdes zera
		InRace = "InRace", -- no Player: true depois de entrar no portal do lobby (ADR 0044)
		-- No personagem: tempo do servidor (workspace:GetServerTimeNow()) em que o gelo mata; nil = não congelado.
		FrozenUntil = "FrozenUntil",
		-- No Player: tempo do servidor em que a corrida atual começou; nil = sem corrida contando.
		RaceStartedAt = "RaceStartedAt",
		-- No Player: tempo (s) da última corrida terminada; nil = ainda não terminou nesta corrida.
		RaceFinishTime = "RaceFinishTime",
		-- No Player: melhor tempo (s) nesta sessão do servidor (placar RF-63); nil = nunca terminou.
		BestTime = "BestTime",
		-- No Player: muda a cada volta instantânea ao checkpoint (zona de morte). Cliente e HookService
		-- soltam o gancho e devolvem os verdes, como ao renascer.
		Respawns = "Respawns",
		-- No personagem: true no modo solo (SoloService). Mecânicas entre jogadores (gancho em jogador,
		-- empurrar) devem ignorar quem está em solo.
		Solo = "Solo",
	},

	-- Modo solo (SoloService): no lugar do "servidor vazio" do DDNet, o jogador vira fantasma para os
	-- outros (sem colisão entre personagens) entre as linhas SoloStart e SoloEnd.
	Solo = {
		PlayersGroup = "Players", -- grupo de colisão de todo personagem
		SoloGroup = "SoloPlayers", -- personagem em solo: não colide com nenhum outro personagem
	},

	-- Zonas: morte e gelo (RF-20..25). Dono: subagente de zonas.
	Freeze = {
		-- Como no DDNet: congelado enquanto toca o freeze; depois de sair, descongela após este tempo
		-- (ou na hora, num unfreeze). Não mata: preso sozinho, o jogador usa o botão de recomeçar.
		ReleaseDelay = 1, -- segundos
		HighlightColor = Color3.fromRGB(150, 220, 255), -- visual local do congelado (FreezeController)
		HighlightFillTransparency = 0.45,
	},
	Zones = {
		CheckInterval = 0, -- segundos entre as conferências das zonas no servidor (0 = todo quadro)
		-- Deslocamento (studs) entre conferências acima do qual é teleporte, não movimento: não varre.
		MaxSweep = 30,
		-- Caixa do corpo usada na conferência, no espaço do HumanoidRootPart (R15 padrão: pés ~3 studs
		-- abaixo do centro do root, topo da cabeça ~2,5 acima).
		CharacterBoxSize = Vector3.new(2, 5.5, 1), -- studs
		CharacterBoxOffsetY = -0.25, -- studs: centro da caixa em relação ao centro do root
		-- Folga em volta da caixa: gelo e descongelar são sólidos, então "tocar" = encostar nesta folga.
		TouchMargin = 0.25, -- studs
	},

	-- Corrida, HUD e placar (RF-60..63). Dono: subagente de corrida.
	RaceUi = {
		Font = Enum.Font.GothamBold,
		TextColor = Color3.fromRGB(255, 255, 255),
		StrokeColor = Color3.fromRGB(0, 0, 0),
		PanelColor = Color3.fromRGB(20, 24, 32),
		PanelTransparency = 0.25,
		CornerRadius = 8, -- pixels

		TimerTextSize = 36, -- pixels
		TimerTopOffset = 12, -- pixels do topo da tela

		FreezeTextSize = 48, -- pixels
		FreezeColor = Color3.fromRGB(140, 220, 255),
		FreezeUrgentTime = 5, -- segundos restantes a partir dos quais o contador fica vermelho
		FreezeUrgentColor = Color3.fromRGB(255, 90, 90),

		LobbyButtonSize = Vector2.new(90, 34), -- pixels
		LobbyButtonColor = Color3.fromRGB(70, 80, 100),

		EndPanelSize = Vector2.new(360, 230), -- pixels
		EndTitleTextSize = 30,
		EndTextSize = 24,
		EndButtonSize = Vector2.new(150, 44), -- pixels
		AgainButtonColor = Color3.fromRGB(60, 170, 90),
		BackButtonColor = Color3.fromRGB(70, 110, 190),
		NewBestColor = Color3.fromRGB(255, 215, 80),

		BoardWidth = 260, -- pixels
		BoardRowHeight = 24, -- pixels
		BoardTextSize = 18,
		BoardMaxRows = 10, -- jogadores mostrados no placar
	},

	Tags = {
		NoHook = "NoHook",
		HookOnce = "HookOnce",
		FreezeZone = "FreezeZone",
		UnfreezeZone = "UnfreezeZone",
		KillZone = "KillZone",
		Checkpoint = "Checkpoint",
		RaceStart = "RaceStart",
		RaceFinish = "RaceFinish",
		BouncerPickup = "BouncerPickup",
		BouncerZone = "BouncerZone",
		LobbySpawn = "LobbySpawn",
		LobbyPortal = "LobbyPortal",
		OneWay = "OneWay", -- mão única (atributo `Config.MapElements.DirectionAttribute`)
		HookThrough = "HookThrough", -- sólido para o jogador, o gancho atravessa
		EditorSpawn = "EditorSpawn", -- no Studio, renasce aqui se `Enabled` (área do MapBuilder)
		StartLine = "StartLine", -- linha de largada: ao entrar, começa/recomeça o tempo da run
		FinishLine = "FinishLine", -- linha de chegada: ao entrar com a run valendo, salva o tempo
		SoloStart = "SoloStart", -- ao entrar: modo solo (fantasma para os outros jogadores)
		SoloEnd = "SoloEnd", -- ao entrar: sai do modo solo
	},

	-- Elementos de mapa do MapBuilder (Shared.MapElements).
	MapElements = {
		DirectionAttribute = "Direction", -- "Up" | "Down" | "Left" | "Right": sentido em que se passa
		-- Folga (studs) para a mão única considerar o personagem do lado sólido.
		OneWayTolerance = 0.6,
		OneWayCheckRadius = 40, -- studs: só confere mãos únicas perto do personagem
		BlockDepth = 12, -- studs: profundidade (Z) dos blocos pintados, como os mapas existentes
		DefaultGrid = 4, -- studs: lado do bloco no MapBuilder
		EditorModelName = "Editor", -- Workspace.Maps.<nome>: onde o MapBuilder pinta
	},
}

return table.freeze(Config)
