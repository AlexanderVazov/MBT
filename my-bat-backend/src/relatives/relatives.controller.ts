import {
  Body,
  Controller,
  Delete,
  Get,
  HttpCode,
  HttpStatus,
  Param,
  Post,
  Request,
  UseGuards,
} from '@nestjs/common';
import { ApiBearerAuth, ApiTags } from '@nestjs/swagger';
import { JwtAuthGuard, RolesGuard } from 'src/auth/guards';
import { RequestWithUser } from 'src/common';
import { RelativesService } from './relatives.service';
import { AcceptInviteDto, CreateRelativeDto, InviteUserDto } from './dtos';

@ApiTags('Relatives')
@ApiBearerAuth('AccessToken')
@UseGuards(JwtAuthGuard, RolesGuard)
@Controller('relatives')
export class RelativesController {
  constructor(private readonly relativesService: RelativesService) {}

  @Post()
  async create(
    @Request() req: RequestWithUser,
    @Body() dto: CreateRelativeDto,
  ) {
    return this.relativesService.create(req.user.id, dto);
  }

  @Get()
  async findAll(@Request() req: RequestWithUser) {
    return this.relativesService.findAllByUser(req.user.id);
  }

  @Delete(':id')
  async remove(@Param('id') id: string, @Request() req: RequestWithUser) {
    return this.relativesService.remove(id, req.user.id);
  }

  @Post('invite')
  @HttpCode(HttpStatus.NO_CONTENT)
  async invite(
    @Request() req: RequestWithUser,
    @Body() dto: InviteUserDto,
  ) {
    return this.relativesService.invite(req.user.id, dto);
  }

  @Post('accept-invite')
  @HttpCode(HttpStatus.NO_CONTENT)
  async acceptInvite(
    @Request() req: RequestWithUser,
    @Body() dto: AcceptInviteDto,
  ) {
    return this.relativesService.acceptInvite(req.user.id, dto);
  }
}
