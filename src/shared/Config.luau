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
		WalkSpeed = 24, -- studs/s (padrão do Roblox: 16)
		-- Pulo normal fica no padrão do Roblox (JumpHeight 7.2, ~50 studs/s de saída).
		DoubleJumpVelocity = 50, -- studs/s para cima no pulo duplo (a queda é zerada antes)
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
	},

	-- Lobby antes do mapa (ADR 0044).
	Lobby = {
		PortalMargin = 1, -- studs de folga em volta do portal em que entrar ainda conta
		CheckInterval = 0.1, -- segundos entre as conferências do portal
	},

	Hook = {
		-- "Pull" = puxão direto ao alvo (ADR 0042, padrão). "Swing" = balanço com RopeConstraint
		-- (ADR 0036), mantido como referência.
		Mode = "Pull",
		Range = 40, -- studs, contados do HumanoidRootPart (ADR 0039)
		Cooldown = 0.25, -- segundos entre um prender e o próximo
		AimAssistRadius = 3, -- studs; raio da esfera de ajuda de mira (ADR 0039)
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
		LandingSlideDecel = 90, -- studs/s²: freio do deslize ao pousar com embalo
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
		SwingAcceleration = 50, -- studs/s² aplicados por A/D enquanto preso (balanço) e no embalo
		MaxSwingSpeed = 70, -- studs/s; limite de velocidade enquanto preso e no embalo
		UprightResponsiveness = 40, -- quão rápido o personagem volta a ficar em pé enquanto preso
		FaceFlipSpeed = 2, -- studs/s em X para o personagem virar para o lado do movimento
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
	},

	Freeze = {
		Duration = 15, -- segundos congelado até morrer (ADR 0014)
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
	},
}

return table.freeze(Config)
