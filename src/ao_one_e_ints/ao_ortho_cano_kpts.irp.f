!todo: add kpts

 BEGIN_PROVIDER [ complex*16, ao_cart_to_sphe_coef_kpts, (ao_num_per_kpt,ao_num_per_kpt)]
&BEGIN_PROVIDER [ integer, ao_cart_to_sphe_num_per_kpt ]
  implicit none
  BEGIN_DOC
! Coefficients to go from cartesian to spherical coordinates in the current
! basis set
  END_DOC
  integer :: i
  integer, external              :: ao_power_index
  integer                        :: ibegin,j,k
  integer                        :: prev
  prev = 0
  ao_cart_to_sphe_coef_kpts(:,:) = (0.d0,0.d0)
  ! Assume order provided by ao_power_index
  i = 1
  ao_cart_to_sphe_num_per_kpt = 0
  do while (i <= ao_num_per_kpt)
    select case ( ao_l(i) )
      case (0)
        ao_cart_to_sphe_num_per_kpt += 1
        ao_cart_to_sphe_coef_kpts(i,ao_cart_to_sphe_num_per_kpt) = (1.d0,0.d0)
        i += 1
      BEGIN_TEMPLATE
      case ($SHELL)
        if (ao_power(i,1) == $SHELL) then
          do k=1,size(cart_to_sphe_$SHELL,2)
            do j=1,size(cart_to_sphe_$SHELL,1)
              ao_cart_to_sphe_coef_kpts(i+j-1,ao_cart_to_sphe_num_per_kpt+k) = dcmplx(cart_to_sphe_$SHELL(j,k),0.d0)
            enddo
          enddo
          i += size(cart_to_sphe_$SHELL,1)
          ao_cart_to_sphe_num_per_kpt += size(cart_to_sphe_$SHELL,2)
        endif
      SUBST [ SHELL ]
        1;;
        2;;
        3;;
        4;;
        5;;
        6;;
        7;;
        8;;
        9;;
      END_TEMPLATE
      case default
        stop 'Error in ao_cart_to_sphe_kpts : angular momentum too high'
    end select
  enddo

END_PROVIDER
!BEGIN_PROVIDER [ integer, ao_cart_to_sphe_num_per_kpt ]
!  implicit none
!  ao_cart_to_sphe_num_per_kpt = ao_cart_to_sphe_num / kpt_num
!END_PROVIDER
!
!BEGIN_PROVIDER [ complex*16, ao_cart_to_sphe_coef_kpts, (ao_num_per_kpt,ao_cart_to_sphe_num_per_kpt) ]
! implicit none
! BEGIN_DOC
! ! complex version of ao_cart_to_sphe_coef for one k-point
! END_DOC
! call zlacp2('A',ao_num_per_kpt,ao_cart_to_sphe_num_per_kpt, &
!        ao_cart_to_sphe_coef,size(ao_cart_to_sphe_coef,1), &
!        ao_cart_to_sphe_coef_kpts,size(ao_cart_to_sphe_coef_kpts,1))
!END_PROVIDER

BEGIN_PROVIDER [ complex*16, ao_cart_to_sphe_overlap_kpts, (ao_cart_to_sphe_num_per_kpt,ao_cart_to_sphe_num_per_kpt,kpt_num) ]
  implicit none
  BEGIN_DOC
  ! AO overlap matrix in the spherical basis set
  END_DOC
  integer :: k
  complex*16, allocatable :: S(:,:)
  allocate (S(ao_cart_to_sphe_num_per_kpt,ao_num_per_kpt))

  !todo: call with (:,:,k) vs (1,1,k)? is there a difference? does one create a temporary array?
  do k=1, kpt_num
   
    call zgemm('T','N',ao_cart_to_sphe_num_per_kpt,ao_num_per_kpt,ao_num_per_kpt, (1.d0,0.d0), &
      ao_cart_to_sphe_coef_kpts,size(ao_cart_to_sphe_coef_kpts,1), &
      ao_overlap_kpts(:,:,k),size(ao_overlap_kpts,1), (0.d0,0.d0), &
      S, size(S,1))
   
    call zgemm('N','N',ao_cart_to_sphe_num_per_kpt,ao_cart_to_sphe_num_per_kpt,ao_num_per_kpt, (1.d0,0.d0), &
      S, size(S,1), &
      ao_cart_to_sphe_coef_kpts,size(ao_cart_to_sphe_coef_kpts,1), (0.d0,0.d0), &
      ao_cart_to_sphe_overlap_kpts(:,:,k),size(ao_cart_to_sphe_overlap_kpts,1))
  enddo 
  deallocate(S)

END_PROVIDER




BEGIN_PROVIDER [ complex*16, ao_ortho_cano_coef_inv_kpts, (ao_num_per_kpt,ao_num_per_kpt, kpt_num)]
 implicit none
 BEGIN_DOC
! ao_ortho_canonical_coef_complex^(-1)
 END_DOC
 integer :: k
 do k=1, kpt_num
   call get_inverse_complex(ao_ortho_canonical_coef_kpts,size(ao_ortho_canonical_coef_kpts,1),&
     ao_num_per_kpt, ao_ortho_cano_coef_inv_kpts, size(ao_ortho_cano_coef_inv_kpts,1))
 enddo
END_PROVIDER

 BEGIN_PROVIDER [ complex*16, ao_ortho_canonical_coef_kpts, (ao_num_per_kpt,ao_num_per_kpt,kpt_num)]
&BEGIN_PROVIDER [ integer, ao_ortho_canonical_num_per_kpt, (kpt_num) ]
&BEGIN_PROVIDER [ integer, ao_ortho_canonical_num_per_kpt_max ]
  implicit none
  BEGIN_DOC
! TODO: ao_ortho_canonical_num_complex should be the same as the real version
!       maybe if the providers weren't linked we could avoid making a complex one?
! matrix of the coefficients of the mos generated by the
! orthonormalization by the S^{-1/2} canonical transformation of the aos
! ao_ortho_canonical_coef(i,j) = coefficient of the ith ao on the jth ao_ortho_canonical orbital
  END_DOC
  integer :: i,k
  ao_ortho_canonical_coef_kpts = (0.d0,0.d0)
  do k=1,kpt_num
    do i=1,ao_num
      ao_ortho_canonical_coef_kpts(i,i,k) = (1.d0,0.d0)
    enddo
  enddo

!call ortho_lowdin(ao_overlap,size(ao_overlap,1),ao_num,ao_ortho_canonical_coef,size(ao_ortho_canonical_coef,1),ao_num)
!ao_ortho_canonical_num=ao_num
!return

  if (ao_cartesian) then

    ao_ortho_canonical_num_per_kpt = ao_num_per_kpt
    do k=1,kpt_num
      call ortho_canonical_complex(ao_overlap_kpts(:,:,k),size(ao_overlap_kpts,1), &
        ao_num_per_kpt,ao_ortho_canonical_coef_kpts(:,:,k),size(ao_ortho_canonical_coef_kpts,1), &
        ao_ortho_canonical_num_per_kpt(k),lin_dep_cutoff)
    enddo


  else

    complex*16, allocatable :: S(:,:)

    allocate(S(ao_cart_to_sphe_num_per_kpt,ao_cart_to_sphe_num_per_kpt))
    do k=1,kpt_num
      S = (0.d0,0.d0)
      do i=1,ao_cart_to_sphe_num_per_kpt
        S(i,i) = (1.d0,0.d0)
      enddo

      ao_ortho_canonical_num_per_kpt(k) = ao_cart_to_sphe_num_per_kpt
      call ortho_canonical_complex(ao_cart_to_sphe_overlap_kpts, size(ao_cart_to_sphe_overlap_kpts,1), &
        ao_cart_to_sphe_num_per_kpt, S, size(S,1), ao_ortho_canonical_num_per_kpt(k),lin_dep_cutoff)

      call zgemm('N','N', ao_num_per_kpt, ao_ortho_canonical_num_per_kpt(k), ao_cart_to_sphe_num_per_kpt, (1.d0,0.d0), &
        ao_cart_to_sphe_coef_kpts, size(ao_cart_to_sphe_coef_kpts,1), &
        S, size(S,1), &
        (0.d0,0.d0), ao_ortho_canonical_coef_kpts(:,:,k), size(ao_ortho_canonical_coef_kpts,1))
    enddo

    deallocate(S)
  endif
  ao_ortho_canonical_num_per_kpt_max = maxval(ao_ortho_canonical_num_per_kpt)
END_PROVIDER

BEGIN_PROVIDER [complex*16, ao_ortho_canonical_overlap_kpts, (ao_ortho_canonical_num_per_kpt_max,ao_ortho_canonical_num_per_kpt_max,kpt_num)]
  implicit none
  BEGIN_DOC
! overlap matrix of the ao_ortho_canonical.
! Expected to be the Identity
  END_DOC
  integer                        :: i,j,k,l,kk
  complex*16               :: c
  do k=1,kpt_num
    do j=1, ao_ortho_canonical_num_per_kpt_max
      do i=1, ao_ortho_canonical_num_per_kpt_max
        ao_ortho_canonical_overlap_kpts(i,j,k) = (0.d0,0.d0)
      enddo
    enddo
  enddo
  do kk=1,kpt_num
    do j=1, ao_ortho_canonical_num_per_kpt(kk)
      do k=1, ao_num_per_kpt
        c = (0.d0,0.d0)
        do l=1, ao_num_per_kpt
          c +=  conjg(ao_ortho_canonical_coef_kpts(l,j,kk)) * ao_overlap_kpts(l,k,kk)
        enddo
        do i=1, ao_ortho_canonical_num_per_kpt(kk)
          ao_ortho_canonical_overlap_kpts(i,j,kk) += ao_ortho_canonical_coef_kpts(k,i,kk) * c
        enddo
      enddo
    enddo
  enddo
END_PROVIDER
