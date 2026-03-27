import { Controller, Get, Request, UseGuards } from '@nestjs/common';
import { ApiBearerAuth, ApiTags } from '@nestjs/swagger';
import { JwtAuthGuard, RolesGuard } from 'src/auth/guards';
import { RequestWithUser } from 'src/common';

import { UsersService } from './users.service';

@ApiTags('Users')
@ApiBearerAuth('AccessToken')
@UseGuards(JwtAuthGuard, RolesGuard)
@Controller('users')
export class UsersController {
  constructor(private readonly usersService: UsersService) {}

  @Get('me')
  async getMe(@Request() req: RequestWithUser) {
    return req.user;
  }
}
