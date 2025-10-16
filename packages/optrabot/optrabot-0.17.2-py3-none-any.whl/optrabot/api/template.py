from optrabot.main import app
from fastapi import APIRouter, HTTPException
from optrabot import config as optrabotcfg
from optrabot.tradetemplate.templatefactory import Template

router = APIRouter(prefix="/api")

@router.get("/templates/")
def get_templates():
	"""
	Returns 
	"""
	config :optrabotcfg.Config = optrabotcfg.appConfig
	try:
		config :optrabotcfg.Config = optrabotcfg.appConfig
		template_list = []
		template_id = 0
		for item in config.getTemplates():
			template : Template = item
			template_list.append({
                "Id": template_id,
                "Name": template.name,
                "Strategy": template.strategy,
                #"Account": template.account,
				"Type": template.getType(),
                "Enabled": template.is_enabled(),
                #"Amount": template.amount,
                #"TakeProfit": template.takeProfit,
                #"StopLoss": template.stopLoss,
                #"MinPremium": template.minPremium,
                #"Wing": template.wing,
                #"AdjustmentStep": template.adjustmentStep
            })
			template_id += 1
		return template_list
		#return {"templates": ["template1", "template2"]}
		pass
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))

@router.get("/templates/{template_id}")
def get_template(template_id: str) -> dict:
	"""
	Returns details for a specific template
	"""
	try:
		templates = optrabotcfg.appConfig.getTemplates()
		template: Template = templates[int(template_id)]
		return {
			"Id": template_id,
			"Name": template.name,
			"Strategy": template.strategy,
			"Type": template.getType(),
			"Enabled": template.is_enabled()
		}
	except KeyError:
		raise HTTPException(status_code=404, detail=f"Template {template_id} not found")
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))

# Include the router in the main app
app.include_router(router)