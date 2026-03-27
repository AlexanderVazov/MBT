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
import {
  ApiBearerAuth,
  ApiOperation,
  ApiParam,
  ApiResponse,
  ApiTags,
} from '@nestjs/swagger';
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
  @ApiOperation({
    summary: 'Create a new relative account and link them to the current user',
  })
  @ApiResponse({
    status: 201,
    description: 'Relative created and linked successfully',
  })
  @ApiResponse({ status: 400, description: 'Validation error' })
  @ApiResponse({ status: 401, description: 'Unauthorized' })
  async create(
    @Request() req: RequestWithUser,
    @Body() dto: CreateRelativeDto,
  ) {
    return this.relativesService.create(req.user.id, dto);
  }

  @Get()
  @ApiOperation({ summary: 'Get all relatives linked to the current user' })
  @ApiResponse({
    status: 200,
    description: 'List of relative links with user details',
  })
  @ApiResponse({ status: 401, description: 'Unauthorized' })
  async findAll(@Request() req: RequestWithUser) {
    return this.relativesService.findAllByUser(req.user.id);
  }

  @Delete(':id')
  @ApiOperation({ summary: 'Remove a relative link by its ID' })
  @ApiParam({
    name: 'id',
    description: 'UUID of the relative link (not the user ID)',
  })
  @ApiResponse({
    status: 200,
    description: 'Relative link removed successfully',
  })
  @ApiResponse({ status: 401, description: 'Unauthorized' })
  async remove(@Param('id') id: string, @Request() req: RequestWithUser) {
    return this.relativesService.remove(id, req.user.id);
  }

  @Post('invite')
  @HttpCode(HttpStatus.NO_CONTENT)
  @ApiOperation({
    summary:
      'Send an email invite to a user to become a relative (token valid for 5 minutes)',
  })
  @ApiResponse({ status: 204, description: 'Invite email sent successfully' })
  @ApiResponse({ status: 400, description: 'Validation error' })
  @ApiResponse({ status: 401, description: 'Unauthorized' })
  async invite(@Request() req: RequestWithUser, @Body() dto: InviteUserDto) {
    return this.relativesService.invite(req.user.id, dto);
  }

  @Post('accept-invite')
  @HttpCode(HttpStatus.NO_CONTENT)
  @ApiOperation({
    summary: 'Accept a relative invite using the token received via email',
  })
  @ApiResponse({
    status: 204,
    description: 'Invite accepted and relative link created',
  })
  @ApiResponse({ status: 400, description: 'Invitation expired' })
  @ApiResponse({ status: 404, description: 'Invitation token not found' })
  @ApiResponse({ status: 401, description: 'Unauthorized' })
  async acceptInvite(
    @Request() req: RequestWithUser,
    @Body() dto: AcceptInviteDto,
  ) {
    return this.relativesService.acceptInvite(req.user.id, dto);
  }
}
