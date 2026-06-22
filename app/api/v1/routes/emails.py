from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from app.api import deps
from app.services.email_service import EmailService
from app.schemas.sale import CustomEmailSend
from app.models.user import User, UserRole

router = APIRouter()

@router.post("/send-custom")
async def send_custom_email(
    email_data: CustomEmailSend,
    background_tasks: BackgroundTasks,
    _current_user: User = Depends(deps.verify_roles([UserRole.ADMIN, UserRole.WORKER])),
):
    try:
        background_tasks.add_task(
            EmailService.send_html_email,
            to_email=email_data.email,
            subject=email_data.subject,
            html_content=email_data.html_content
        )
        return {"message": "Correo electrónico promocional encolado para envío"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al programar el envío de correo: {str(e)}")
