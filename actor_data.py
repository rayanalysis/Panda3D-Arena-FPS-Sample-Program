from direct.actor.Actor import Actor

player_character = Actor("models/npc_1.bam",
              {"walking": "models/npc_1_ArmatureAction.bam", "death": "models/npc_1_death.bam"})

NPC_1 = Actor("models/npc_1.bam",
              {"walking": "models/npc_1_ArmatureAction.bam", "death": "models/npc_1_death.bam"})
              
arm_handgun = Actor("models/arm_handgun.bam",
              {"shoot": "models/arm_handgun_ArmatureAction.bam"})
