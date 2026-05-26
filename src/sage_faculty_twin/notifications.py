from __future__ import annotations

import smtplib
from email.message import EmailMessage

from .config import AppSettings
from .models import BookingRecord


class BookingNotificationError(RuntimeError):
    pass


class BookingEmailNotifier:
    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings

    def send_booking_request_notification(self, booking: BookingRecord) -> str:
        recipient = self._settings.booking_notification_email.strip()
        if not recipient:
            raise BookingNotificationError("未配置预约提醒收件邮箱。")
        message = self._build_message(
            recipient=recipient,
            subject=f"[Faculty Twin] 新预约申请：{booking.topic}",
            lines=[
                "收到一条新的会议预约申请，请登录管理员界面确认。",
                f"预约编号：{booking.booking_id}",
                f"学生姓名：{booking.student_name}",
                f"学生邮箱：{booking.student_email}",
                f"会议主题：{booking.topic}",
                (
                    "会议时间："
                    f"{booking.start_at.strftime('%Y-%m-%d %H:%M')} - "
                    f"{booking.end_at.strftime('%H:%M')}"
                ),
                f"当前状态：{booking.status}",
            ],
        )
        self._deliver(message)
        return recipient

    def send_booking_approved_notification(self, booking: BookingRecord) -> str:
        recipient = booking.student_email.strip()
        if not recipient:
            raise BookingNotificationError("预约记录缺少学生邮箱，无法发送确认邮件。")

        message = self._build_message(
            recipient=recipient,
            subject=f"[Faculty Twin] 预约已确认：{booking.topic}",
            lines=[
                f"你好，{booking.student_name}：",
                "你的会议预约已经通过管理员确认。",
                f"预约编号：{booking.booking_id}",
                f"会议主题：{booking.topic}",
                (
                    "会议时间："
                    f"{booking.start_at.strftime('%Y-%m-%d %H:%M')} - "
                    f"{booking.end_at.strftime('%H:%M')}"
                ),
                f"当前状态：{booking.status}",
                "会前建议准备：agenda、当前 blocker、已有 draft/结果、以及最想确认的 2-3 个具体问题。",
                "如果这次沟通和课程材料或论文阅读相关，建议提前把对应资料链接或页码整理好，便于会前快速对齐。",
            ],
        )
        self._deliver(message)
        return recipient

    def send_booking_rejected_notification(self, booking: BookingRecord) -> str:
        recipient = booking.student_email.strip()
        if not recipient:
            raise BookingNotificationError("预约记录缺少学生邮箱，无法发送拒绝通知邮件。")

        message = self._build_message(
            recipient=recipient,
            subject=f"[Faculty Twin] 预约未通过：{booking.topic}",
            lines=[
                f"你好，{booking.student_name}：",
                "你的会议预约目前未通过管理员确认，请重新选择时间后再次提交。",
                f"预约编号：{booking.booking_id}",
                f"会议主题：{booking.topic}",
                (
                    "原申请时间："
                    f"{booking.start_at.strftime('%Y-%m-%d %H:%M')} - "
                    f"{booking.end_at.strftime('%H:%M')}"
                ),
                f"当前状态：{booking.status}",
            ],
        )
        self._deliver(message)
        return recipient

    def send_follow_up_email(self, recipient: str, subject: str, lines: list[str]) -> str:
        normalized_recipient = recipient.strip()
        if not normalized_recipient:
            raise BookingNotificationError("缺少收件邮箱，无法发送后续跟进邮件。")
        message = self._build_message(recipient=normalized_recipient, subject=subject, lines=lines)
        self._deliver(message)
        return normalized_recipient

    def _build_message(self, *, recipient: str, subject: str, lines: list[str]) -> EmailMessage:
        self._validate_transport()
        sender = (self._settings.smtp_sender or self._settings.smtp_username or recipient).strip()
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = sender
        message["To"] = recipient
        message.set_content("\n".join(lines))
        return message

    def _validate_transport(self) -> None:
        if not self._settings.smtp_host:
            raise BookingNotificationError("未配置 SMTP 主机，无法发送预约提醒邮件。")
        if self._settings.smtp_use_ssl and self._settings.smtp_use_tls:
            raise BookingNotificationError("SMTP SSL 与 STARTTLS 不能同时启用。")

    def _transport_label(self) -> str:
        if self._settings.smtp_use_ssl:
            return "SSL"
        if self._settings.smtp_use_tls:
            return "STARTTLS"
        return "PLAIN"

    def _format_delivery_error(self, exc: Exception) -> str:
        detail = str(exc).strip() or exc.__class__.__name__
        return (
            "发送预约提醒失败："
            f"连接 SMTP {self._settings.smtp_host}:{self._settings.smtp_port}"
            f"（{self._transport_label()}，超时 {self._settings.smtp_timeout_seconds} 秒）时出现 "
            f"{exc.__class__.__name__}: {detail}"
        )

    def _deliver(self, message: EmailMessage) -> None:
        try:
            if self._settings.smtp_use_ssl:
                with smtplib.SMTP_SSL(
                    self._settings.smtp_host,
                    self._settings.smtp_port,
                    timeout=self._settings.smtp_timeout_seconds,
                ) as server:
                    self._login_if_needed(server)
                    server.send_message(message)
            else:
                with smtplib.SMTP(
                    self._settings.smtp_host,
                    self._settings.smtp_port,
                    timeout=self._settings.smtp_timeout_seconds,
                ) as server:
                    if self._settings.smtp_use_tls:
                        server.starttls()
                    self._login_if_needed(server)
                    server.send_message(message)
        except OSError as exc:
            raise BookingNotificationError(self._format_delivery_error(exc)) from exc
        except smtplib.SMTPException as exc:
            raise BookingNotificationError(self._format_delivery_error(exc)) from exc

    def _login_if_needed(self, server: smtplib.SMTP) -> None:
        if self._settings.smtp_username:
            server.login(self._settings.smtp_username, self._settings.smtp_password or "")