///////////////////////////////////////////////////////////////////////////////
// BSD 3-Clause License
//
// Copyright (C) 2019-2025, University of Edinburgh, LAAS-CNRS,
//                          Heriot-Watt University
// Copyright note valid unless otherwise stated in individual files.
// All rights reserved.
///////////////////////////////////////////////////////////////////////////////

#ifndef CROCODDYL_LEGGED_ROBOTS_FACTORY_HPP_
#define CROCODDYL_LEGGED_ROBOTS_FACTORY_HPP_

#include <pinocchio/parsers/srdf.hpp>
#include <pinocchio/parsers/urdf.hpp>

#include "crocoddyl/core/costs/cost-sum.hpp"
#include "crocoddyl/core/costs/residual.hpp"
#include "crocoddyl/core/integrator/euler.hpp"
#include "crocoddyl/core/residuals/control.hpp"
#include "crocoddyl/multibody/actions/contact-fwddyn.hpp"
#include "crocoddyl/multibody/actuations/floating-base.hpp"
#include "crocoddyl/multibody/contacts/contact-3d.hpp"
#include "crocoddyl/multibody/contacts/contact-6d.hpp"
#include "crocoddyl/multibody/contacts/multiple-contacts.hpp"
#include "crocoddyl/multibody/residuals/com-position.hpp"
#include "crocoddyl/multibody/residuals/frame-placement.hpp"
#include "crocoddyl/multibody/residuals/frame-translation.hpp"
#include "crocoddyl/multibody/residuals/state.hpp"
#include "crocoddyl/multibody/states/multibody.hpp"
#include "robot-ee-names.hpp"

namespace crocoddyl {
namespace benchmark {

template <typename Scalar>
void build_contact_action_models(
    RobotEENames robotNames,
    std::shared_ptr<crocoddyl::ActionModelAbstractTpl<Scalar> >& runningModel,
    std::shared_ptr<crocoddyl::ActionModelAbstractTpl<Scalar> >&
        terminalModel) {
  typedef
      typename crocoddyl::DifferentialActionModelContactFwdDynamicsTpl<Scalar>
          DifferentialActionModelContactFwdDynamics;
  typedef typename crocoddyl::IntegratedActionModelEulerTpl<Scalar>
      IntegratedActionModelEuler;
  typedef typename crocoddyl::ActuationModelFloatingBaseTpl<Scalar>
      ActuationModelFloatingBase;
  typedef typename crocoddyl::CostModelSumTpl<Scalar> CostModelSum;
  typedef typename crocoddyl::ContactModelMultipleTpl<Scalar>
      ContactModelMultiple;
  typedef typename crocoddyl::CostModelAbstractTpl<Scalar> CostModelAbstract;
  typedef typename crocoddyl::ContactModelAbstractTpl<Scalar>
      ContactModelAbstract;
  typedef typename crocoddyl::CostModelResidualTpl<Scalar> CostModelResidual;
  typedef typename crocoddyl::ResidualModelFramePlacementTpl<Scalar>
      ResidualModelFramePlacement;
  typedef typename crocoddyl::ResidualModelCoMPositionTpl<Scalar>
      ResidualModelCoMPosition;
  typedef typename crocoddyl::ResidualModelStateTpl<Scalar> ResidualModelState;
  typedef typename crocoddyl::ResidualModelControlTpl<Scalar>
      ResidualModelControl;
  typedef typename crocoddyl::ContactModel6DTpl<Scalar> ContactModel6D;
  typedef typename crocoddyl::ContactModel3DTpl<Scalar> ContactModel3D;
  typedef typename crocoddyl::MathBaseTpl<Scalar>::Vector2s Vector2s;
  typedef typename crocoddyl::MathBaseTpl<Scalar>::Vector3s Vector3s;
  typedef typename crocoddyl::MathBaseTpl<Scalar>::VectorXs VectorXs;
  typedef typename crocoddyl::MathBaseTpl<Scalar>::Matrix3s Matrix3s;

  pinocchio::ModelTpl<double> modeld;
  pinocchio::urdf::buildModel(robotNames.urdf_path,
                              pinocchio::JointModelFreeFlyer(), modeld);
  modeld.lowerPositionLimit.head<7>().array() = -1;
  modeld.upperPositionLimit.head<7>().array() = 1.;
  pinocchio::srdf::loadReferenceConfigurations(modeld, robotNames.srdf_path,
                                               false);

  pinocchio::ModelTpl<Scalar> model(modeld.cast<Scalar>());
  std::shared_ptr<crocoddyl::StateMultibodyTpl<Scalar> > state =
      std::make_shared<crocoddyl::StateMultibodyTpl<Scalar> >(
          std::make_shared<pinocchio::ModelTpl<Scalar> >(model));

  VectorXs default_state(model.nq + model.nv);
  default_state << model.referenceConfigurations[robotNames.reference_conf],
      VectorXs::Zero(model.nv);

  std::shared_ptr<ActuationModelFloatingBase> actuation =
      std::make_shared<ActuationModelFloatingBase>(state);

  std::shared_ptr<CostModelAbstract> comCost =
      std::make_shared<CostModelResidual>(
          state, std::make_shared<ResidualModelCoMPosition>(
                     state, Vector3s::Zero(), actuation->get_nu()));
  std::shared_ptr<CostModelAbstract> goalTrackingCost =
      std::make_shared<CostModelResidual>(
          state, std::make_shared<ResidualModelFramePlacement>(
                     state, model.getFrameId(robotNames.ee_name),
                     pinocchio::SE3Tpl<Scalar>(
                         Matrix3s::Identity(),
                         Vector3s(Scalar(.0), Scalar(.0), Scalar(.4))),
                     actuation->get_nu()));
  std::shared_ptr<CostModelAbstract> xRegCost =
      std::make_shared<CostModelResidual>(
          state, std::make_shared<ResidualModelState>(state, default_state,
                                                      actuation->get_nu()));
  std::shared_ptr<CostModelAbstract> uRegCost =
      std::make_shared<CostModelResidual>(
          state,
          std::make_shared<ResidualModelControl>(state, actuation->get_nu()));

  // Create a cost model per the running and terminal action model.
  std::shared_ptr<CostModelSum> runningCostModel =
      std::make_shared<CostModelSum>(state, actuation->get_nu());
  std::shared_ptr<CostModelSum> terminalCostModel =
      std::make_shared<CostModelSum>(state, actuation->get_nu());

  // Then let's added the running and terminal cost functions
  runningCostModel->addCost("gripperPose", goalTrackingCost, Scalar(1));
  //   runningCostModel->addCost("comPos", comCost, Scalar(1e-7));
  runningCostModel->addCost("xReg", xRegCost, Scalar(1e-4));
  runningCostModel->addCost("uReg", uRegCost, Scalar(1e-4));
  terminalCostModel->addCost("gripperPose", goalTrackingCost, Scalar(1));

  std::shared_ptr<ContactModelMultiple> contact_models =
      std::make_shared<ContactModelMultiple>(state, actuation->get_nu());

  for (std::size_t i = 0; i < robotNames.contact_names.size(); ++i) {
    switch (robotNames.contact_types[i]) {
      case Contact3D: {
        std::shared_ptr<ContactModelAbstract> support_contact =
            std::make_shared<ContactModel3D>(
                state, model.getFrameId(robotNames.contact_names[i]),
                Eigen::Vector3d::Zero(), pinocchio::LOCAL_WORLD_ALIGNED,
                actuation->get_nu(), Vector2s(Scalar(0.), Scalar(50.)));
        contact_models->addContact(
            model.frames[model.getFrameId(robotNames.contact_names[i])].name,
            support_contact);
        break;
      }
      case Contact6D: {
        std::shared_ptr<ContactModelAbstract> support_contact =
            std::make_shared<ContactModel6D>(
                state, model.getFrameId(robotNames.contact_names[i]),
                pinocchio::SE3Tpl<Scalar>::Identity(),
                pinocchio::LOCAL_WORLD_ALIGNED, actuation->get_nu(),
                Vector2s(Scalar(0.), Scalar(50.)));
        contact_models->addContact(
            model.frames[model.getFrameId(robotNames.contact_names[i])].name,
            support_contact);
        break;
      }
      default: {
        break;
      }
    }
  }

  // Next, we need to create an action model for running and terminal nodes
  std::shared_ptr<DifferentialActionModelContactFwdDynamics> runningDAM =
      std::make_shared<DifferentialActionModelContactFwdDynamics>(
          state, actuation, contact_models, runningCostModel);
  std::shared_ptr<DifferentialActionModelContactFwdDynamics> terminalDAM =
      std::make_shared<DifferentialActionModelContactFwdDynamics>(
          state, actuation, contact_models, terminalCostModel);

  runningModel =
      std::make_shared<IntegratedActionModelEuler>(runningDAM, Scalar(5e-3));
  terminalModel =
      std::make_shared<IntegratedActionModelEuler>(terminalDAM, Scalar(5e-3));
}

}  // namespace benchmark
}  // namespace crocoddyl

#endif  // CROCODDYL_BIPED_FACTORY_HPP_
