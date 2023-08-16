BEGIN_PROVIDER [ double precision, tc_two_rdm, (mo_num, mo_num, mo_num, mo_num)]
 implicit none
 BEGIN_DOC
 ! tc_two_rdm(p,s,q,r) = <Phi| a^dager_p
 END_DOC
 integer :: i,j,istate,m,mm,nn
 integer                        :: exc(0:2,2,2)
 double precision               :: phase
 double precision               :: contrib
 integer                        :: h1,p1,s1,h2,p2,s2,degree
 integer, allocatable           :: occ(:,:)
 integer                        :: n_occ_ab(2),other_spin(2)
 other_spin(1) = 2
 other_spin(2) = 1
 allocate(occ(N_int*bit_kind_size,2))
 tc_two_rdm = 0.d0

 do i = 1, N_det ! psi_left 
  do j = 1, N_det ! psi_right 
   call get_excitation_degree(psi_det(1,1,i),psi_det(1,1,j),degree,N_int)
   if(degree.gt.2)cycle
   if(degree.gt.0)then
    ! get excitation operators: from psi_det(j) --> psi_det(i)
    call get_excitation(psi_det(1,1,j),psi_det(1,1,i),exc,degree,phase,N_int)
    call decode_exc(exc,degree,h1,p1,h2,p2,s1,s2)
    contrib = psi_l_coef_bi_ortho(i,1) * psi_r_coef_bi_ortho(j,1) * phase * state_average_weight(1)
    do istate = 2, N_states
     contrib += psi_l_coef_bi_ortho(i,istate) * psi_r_coef_bi_ortho(j,istate) * phase * state_average_weight(istate)
    enddo
    if(degree == 2)then
     call update_tc_rdm(h1,p1,h2,p2,s1,s2,tc_two_rdm,mo_num,contrib)
    else if(degree==1)then
!     cycle
     ! occupation of the determinant psi_det(j)
     call bitstring_to_list_ab(psi_det(1,1,j), occ, n_occ_ab, N_int) 
 
     ! run over the electrons of opposite spin than the excitation
     s2 = other_spin(s1)
     do mm = 1, n_occ_ab(s2) 
      m = occ(mm,s2)
      h2 = m 
      p2 = m 
      call update_tc_rdm(h1,p1,h2,p2,s1,s2,tc_two_rdm,mo_num,contrib)
     enddo
     ! run over the electrons of same spin than the excitation
     s2 = s1
     do mm = 1, n_occ_ab(s2) 
      m = occ(mm,s2)
      h2 = m 
      p2 = m 
      if(h2.le.h1)cycle
      call update_tc_rdm(h1,p1,h2,p2,s1,s2,tc_two_rdm,mo_num,contrib)
     enddo
    endif
   else if(degree == 0)then
    contrib = psi_l_coef_bi_ortho(i,1) * psi_r_coef_bi_ortho(j,1) *  state_average_weight(1)
!    print*,'contrib',contrib
    do istate = 2, N_states
     contrib += psi_l_coef_bi_ortho(i,istate) * psi_r_coef_bi_ortho(j,istate) *  state_average_weight(istate)
    enddo
    ! occupation of the determinant psi_det(j)
    call bitstring_to_list_ab(psi_det(1,1,j), occ, n_occ_ab, N_int) 
    s1 = 1 ! alpha electrons
     do nn = 1, n_occ_ab(s1)
      h1 = occ(nn,s1)
      p1 = occ(nn,s1)
      ! run over the couple of alpha-beta electrons 
      s2 = other_spin(s1)
      do mm = 1, n_occ_ab(s2) 
       m = occ(mm,s2)
       h2 = m 
       p2 = m 
       call update_tc_rdm(h1,p1,h2,p2,s1,s2,tc_two_rdm,mo_num,contrib)
      enddo
      ! run over the couple of alpha-alpha electrons 
      s2 = s1
      do mm = 1, n_occ_ab(s2) 
       m = occ(mm,s2)
       h2 = m 
       p2 = m 
       if(h2.le.h1)cycle
       call update_tc_rdm(h1,p1,h2,p2,s1,s2,tc_two_rdm,mo_num,contrib)
      enddo
    enddo
    s1 = 2
     do nn = 1, n_occ_ab(s1)
      h1 = occ(nn,s1)
      p1 = occ(nn,s1)
      ! run over the couple of beta-beta electrons 
      s2 = s1
      do mm = 1, n_occ_ab(s2) 
       m = occ(mm,s2)
       h2 = m 
       p2 = m 
       if(h2.le.h1)cycle
       call update_tc_rdm(h1,p1,h2,p2,s1,s2,tc_two_rdm,mo_num,contrib)
      enddo
    enddo
   endif
  enddo
 enddo

END_PROVIDER 

subroutine update_tc_rdm(h1,p1,h2,p2,s1,s2,array,sze,contrib)
 implicit none
 integer, intent(in) :: h1,p1,h2,p2,s1,s2,sze
 double precision, intent(in) :: contrib
 double precision, intent(inout) :: array(sze, sze, sze, sze)
 integer :: istate
 if(s1.ne.s2)then
   array(p1,h1,p2,h2) += contrib
   ! permutation for particle symmetry
   array(p2,h2,p1,h1) += contrib
 else ! same spin double excitation 
   array(p1,h1,p2,h2) += contrib
   ! exchange 
   ! exchanging the holes 
   array(p2,h1,p1,h2) -= contrib
   ! exchanging the particles 
   array(p1,h2,p2,h1) -= contrib

   ! permutation for particle symmetry
   array(p2,h2,p1,h1) += contrib
   ! exchange 
   ! exchanging the holes 
   array(p1,h2,p2,h1) -= contrib
   ! exchanging the particles 
   array(p2,h1,p1,h2) -= contrib
 endif

end
