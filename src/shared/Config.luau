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

	Checkpoint = {
		ZoneHeight = 10, -- studs acima da peça em que o checkpoint ainda conta
		SpawnHeight = 4, -- studs acima da peça onde o jogador renasce
	},

	Race = {
		RespawnTime = 1, -- segundos entre morrer e renascer
	},

	Hook = {
		-- "Swing" = balanço com RopeConstraint (ADR 0036). "Pull" (puxão) é o plano B: ainda não existe.
		Mode = "Swing",
		Range = 40, -- studs, contados do HumanoidRootPart (ADR 0039)
		Cooldown = 0.25, -- segundos entre um prender e o próximo
		PullStrength = 120, -- reservado para o modo "Pull" (plano B); o balanço não usa
		AimAssistRadius = 3, -- studs; raio da esfera de ajuda de mira (ADR 0039)
		SurfaceTolerance = 0.5, -- studs: folga para o ponto atingido contar como "na peça, no plano"
		-- Peças com CanCollide = false (volumes de zona, enfeites) não prendem.
		IgnoreNonCollidable = true,

		-- Corda (RF-18)
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

		-- Balanço (RF-17)
		SwingAcceleration = 50, -- studs/s² aplicados por A/D enquanto preso e no embalo
		MaxSwingSpeed = 90, -- studs/s; limite de velocidade enquanto preso e no embalo
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
	},
}

return table.freeze(Config)
