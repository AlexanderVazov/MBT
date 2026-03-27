import {
  Body,
  Controller,
  Post,
  Req,
  Request,
  UseGuards,
} from '@nestjs/common';
import { RequestWithUser } from 'src/common';
import { ApiBearerAuth, ApiBody, ApiTags } from '@nestjs/swagger';

import { LocalAuthGuard, RefreshAuthGuard } from './guards';
import { LoginDto, RegisterDto, RequestWithSession } from './dtos';
import { AuthService } from './auth.service';

@ApiTags('Auth')
@Controller('auth')
export class AuthController {
  constructor(private readonly authService: AuthService) {}

  @Post('register')
  async register(@Body() dto: RegisterDto) {
    return await this.authService.register(dto);
  }

  @UseGuards(LocalAuthGuard)
  @ApiBody({ type: LoginDto })
  @Post('login')
  async login(@Request() req: RequestWithUser) {
    return await this.authService.login(req.user);
  }

  @ApiBearerAuth('RefreshToken')
  @UseGuards(RefreshAuthGuard)
  @Post('refresh')
  async refreshTokens(@Req() req: RequestWithSession) {
    return await this.authService.refreshTokens(req.user.session);
  }
}
